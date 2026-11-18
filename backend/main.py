import hmac
import os
import signal
import socket
import sqlite3
import sys
import threading
import re
import math
import json
import urllib.error
import urllib.parse
import urllib.request
import ssl
import truststore
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import platform
from pathlib import Path

# Modules voisins (fits.py), y compris quand Python est lancé en mode isolé (-I)
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fits  # noqa: E402

# L'encodage Windows par défaut ferait planter print() sur certains noms d'utilisateur
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Vrai uniquement pour le binaire PyInstaller lancé par Tauri (pas en développement)
IS_SIDECAR = getattr(sys, "frozen", False)

# Jeton généré par l'application à chaque lancement
API_TOKEN = os.environ.get("ALLNIGHTLONG_TOKEN", "")
if IS_SIDECAR and not API_TOKEN:
    sys.exit("ALLNIGHTLONG_TOKEN manquant : démarrage refusé.")

app = FastAPI()

@app.middleware("http")
async def require_token(request: Request, call_next):
    if API_TOKEN:
        authorization = request.headers.get("authorization", "")
        if not hmac.compare_digest(authorization.encode(), f"Bearer {API_TOKEN}".encode()):
            return JSONResponse({"detail": "Non autorisé"}, status_code=401)
    return await call_next(request)

# Configuration CORS : seule l'interface Tauri peut appeler l'API depuis un navigateur.
# Ajouté après require_token pour traiter les requêtes de pré-vérification en premier.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "tauri://localhost",        # macOS / Linux
        "http://tauri.localhost",   # Windows
        "http://localhost:5173",    # Développement
    ],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

def self_terminate():
    os.kill(os.getpid(), signal.SIGTERM)

# Tauri garde stdin ouvert : sa fermeture signifie que l'application n'existe plus
def exit_when_parent_dies():
    sys.stdin.read()
    os._exit(0)


def get_db_path() -> str:
    app_name = "allnightlong"
    system = platform.system()
    
    if system == "Windows":
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            base_dir = os.path.expanduser("~")
    elif system == "Darwin": # macOS
        base_dir = os.path.expanduser("~/Library/Application Support")
    else: # Linux / Autre
        base_dir = os.environ.get("XDG_DATA_HOME")
        if not base_dir:
            base_dir = os.path.expanduser("~/.local/share")
            
    # Créer le dossier de l'application s'il n'existe pas encore
    db_dir = Path(base_dir) / app_name
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Renvoie le chemin absolu vers le fichier de la BDD
    return str(db_dir / "allnightlong.db")

# Initialisation du chemin vers un dossier utilisateur autorisé en écriture
DB_PATH = get_db_path()
print(f"Base de données SQLite initialisée à : {DB_PATH}")

# ================= MODÈLES DE DONNÉES (Validation) =================
class TargetSchema(BaseModel):
    id: Optional[int] = None
    name: str
    usualName: str = ""
    constellation: str = ""
    otherDesignations: str = ""
    type: str = ""
    group: str = ""
    magnitude: str = ""
    colorIndex: str = ""
    surfBrightness: str = ""
    size: str = ""
    ra: str = ""
    dec: str = ""
    imageRef: str = ""
    notes: str = ""

# Une cible vue dans une observation : la hauteur et les poses retenues lui sont propres
class ObservationTargetSchema(BaseModel):
    targetId: int
    altitude: str = ""
    imgGood: int = 0
    imgPass: int = 0
    imgBad: int = 0
    notes: str = ""

class ObservationSchema(BaseModel):
    id: Optional[int] = None
    # Date et heure TU complètes, "AAAA-MM-JJ HH:MM" (l'heure peut manquer sur d'anciennes fiches)
    start: str
    end: str = ""
    # Lieu et Bortle sont ceux de la session (une nuit dans un lieu), partagés par ses observations
    locationId: Optional[int] = None
    bortle: Optional[float] = None
    sessionId: Optional[int] = None
    nightDate: str = ""
    instrument: str = ""
    sensor: str = ""
    filter: str = ""
    sensorTemp: str = ""
    subExposure: str = ""
    imgTotal: int = 0
    notes: str = ""
    # Lieu saisi en texte libre avant les lieux enregistrés, conservé jusqu'à sa conversion
    legacyLocation: str = ""
    targets: List[ObservationTargetSchema] = []
    images: List["ObservationImageSchema"] = []

# Une image d'une observation. "path" est toujours un chemin complet côté API ;
# en base, il est relatif au dossier des images quand l'image s'y trouve.
class ObservationImageSchema(BaseModel):
    id: Optional[int] = None
    path: str
    kind: str = "traitée"
    software: str = ""
    palette: str = ""
    caption: str = ""
    isFavorite: bool = False
    # Cibles visibles sur l'image ; aucune = champ entier
    targetIds: List[int] = []
    # Calculé à la lecture : le fichier n'existe pas (disque débranché, dossier déplacé…)
    missing: bool = False

class SettingsSchema(BaseModel):
    imagesFolder: str = ""
    # Marge (en heures) ajoutée avant et après le créneau des observations pour la météo
    weatherMarginHours: int = 1

# Relevé météo horaire d'une session (une nuit dans un lieu)
class WeatherReadingSchema(BaseModel):
    time: str  # "AAAA-MM-JJ HH:MM", TU
    cloudLow: Optional[float] = None
    cloudMid: Optional[float] = None
    cloudHigh: Optional[float] = None
    seeing: Optional[float] = None
    index1: Optional[float] = None
    index2: Optional[float] = None
    jetStream: Optional[float] = None
    temp: Optional[float] = None
    humidity: Optional[float] = None
    dewPoint: Optional[float] = None
    # open-meteo, meteoblue ou manuel ; "edited" protège une valeur corrigée du rafraîchissement
    source: str = "manuel"
    edited: bool = False

ObservationSchema.model_rebuild()

class LocationSchema(BaseModel):
    id: Optional[int] = None
    label: str
    lat: float
    lon: float
    elevationM: Optional[float] = None
    bortle: Optional[float] = None
    notes: str = ""


class ExportRequest(BaseModel):
    path: str


# ================= SAUVEGARDES =================
def backup_db(destination: str):
    # Fichier temporaire : une copie interrompue n'abîme jamais une sauvegarde existante
    temp_path = f"{destination}.tmp"
    source = sqlite3.connect(DB_PATH)
    target = sqlite3.connect(temp_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    os.replace(temp_path, destination)

def backup_before_migration(version: int):
    backup_dir = Path(DB_PATH).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination = backup_dir / f"allnightlong-v{version}-{timestamp}.db"
    backup_db(str(destination))
    print(f"Sauvegarde avant migration : {destination}")


# ================= DATES ET SESSIONS =================
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def night_of(start: str) -> str:
    """Nuit d'une observation : une observation commencée avant midi appartient à la nuit de la veille."""
    day = datetime.strptime(start[:10], "%Y-%m-%d")
    if len(start) > 10 and start[11:13] < "12":
        day -= timedelta(days=1)
    return day.strftime("%Y-%m-%d")

def legacy_start_end(date: str, obs_start: str, obs_end: str):
    """Ancien format (date + heures) : la date est prise comme celle du début, la fin passe au
    lendemain si elle précède le début. Les dates exactes seront reprises des FITS (lot Migration)."""
    start = f"{date} {obs_start}" if obs_start else date
    if not obs_end:
        return start, ""
    end_day = datetime.strptime(date, "%Y-%m-%d")
    if obs_start and obs_end < obs_start:
        end_day += timedelta(days=1)
    return start, f"{end_day:%Y-%m-%d} {obs_end}"

def find_or_create_session(cursor, night_date: str, location_id, bortle):
    cursor.execute("SELECT id FROM sessions WHERE night_date = ? AND location_id IS ?", (night_date, location_id))
    row = cursor.fetchone()
    if row:
        if bortle is not None:
            cursor.execute("UPDATE sessions SET bortle = ? WHERE id = ?", (bortle, row[0]))
        return row[0]
    if bortle is None and location_id is not None:
        default = cursor.execute("SELECT bortle FROM locations WHERE id = ?", (location_id,)).fetchone()
        bortle = default[0] if default else None
    cursor.execute("INSERT INTO sessions (night_date, location_id, bortle) VALUES (?, ?, ?)", (night_date, location_id, bortle))
    return cursor.lastrowid

def delete_empty_sessions(cursor):
    cursor.execute("DELETE FROM sessions WHERE id NOT IN (SELECT session_id FROM observations WHERE session_id IS NOT NULL)")


# ================= RÉGLAGES ET CHEMINS D'IMAGES =================
def read_setting(conn, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default

def write_setting(cursor, key: str, value: str):
    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))

def images_folder(conn) -> str:
    return read_setting(conn, "images_folder")

def weather_margin(conn) -> int:
    try:
        return int(read_setting(conn, "weather_margin_hours", "1"))
    except ValueError:
        return 1

def is_web_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))

def to_stored_path(path: str, folder: str) -> str:
    """Chemin enregistré : relatif au dossier des images quand l'image s'y trouve, complet sinon."""
    if not path or is_web_url(path) or not folder or not os.path.isabs(path):
        return path
    try:
        relative = os.path.relpath(path, folder)
    except ValueError:  # autre lecteur
        return path
    return path if relative.startswith("..") else relative

def to_full_path(path: str, folder: str) -> str:
    if not path or is_web_url(path) or os.path.isabs(path) or not folder:
        return path
    return os.path.join(folder, path)

def file_missing(full_path: str) -> bool:
    return bool(full_path) and not is_web_url(full_path) and not os.path.isfile(full_path)


# Classement des anciennes images d'après leur nom de fichier (migration v5)
def guess_image_details(path: str):
    name = os.path.basename(path).lower()
    stem = os.path.splitext(name)[0]
    kind = "astrométrie" if "astrom" in name else "traitée"
    software = "Siril" if "siril" in name else "Stacking Wizard" if "wizard" in name else ""
    palette = "Dual band" if "duoband" in name else "Naturelle" if "natur" in name else "RVB" if "rgb" in name else ""
    caption = "Finition Photoshop" if stem.rstrip("()0123456789").endswith("ps") else ""
    return kind, software, palette, caption


# ================= INITIALISATION & MIGRATIONS =================
LATEST_SCHEMA_VERSION = 7

def migrate_to_v4(conn):
    # Reconstruction de la table observations : SQLite ne sait pas retirer une clé étrangère.
    # Les contraintes sont suspendues le temps de la copie, en une seule transaction.
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF;")
    cursor = conn.cursor()
    cursor.execute("BEGIN")
    cursor.execute("""
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            night_date TEXT NOT NULL,
            location_id INTEGER REFERENCES locations (id) ON DELETE SET NULL,
            bortle REAL
        );
    """)
    cursor.execute("""
        CREATE TABLE observations_v4 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES sessions (id),
            start_utc TEXT NOT NULL,
            end_utc TEXT DEFAULT '',
            instrument TEXT DEFAULT '',
            sensor TEXT,
            filter TEXT,
            sensor_temp TEXT,
            sub_exposure TEXT,
            img_total INTEGER,
            notes TEXT DEFAULT '',
            image_raw TEXT,
            image_processed TEXT,
            legacy_location TEXT DEFAULT ''
        );
    """)
    cursor.execute("""
        CREATE TABLE observation_targets (
            observation_id INTEGER NOT NULL REFERENCES observations (id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES targets (id) ON DELETE CASCADE,
            altitude TEXT DEFAULT '',
            img_good INTEGER DEFAULT 0,
            img_pass INTEGER DEFAULT 0,
            img_bad INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            PRIMARY KEY (observation_id, target_id)
        );
    """)

    rows = cursor.execute("""
        SELECT id, target_id, date, obs_start, obs_end, location, altitude, sensor, filter, sensor_temp, sub_exposure,
               img_total, img_good, img_pass, img_bad, other_objects, image_raw, image_processed, location_id
        FROM observations
    """).fetchall()
    for (obs_id, target_id, date, obs_start, obs_end, location, altitude, sensor, filter_, sensor_temp, sub_exposure,
         img_total, img_good, img_pass, img_bad, notes, image_raw, image_processed, location_id) in rows:
        start, end = legacy_start_end(date, obs_start or "", obs_end or "")
        session_id = find_or_create_session(cursor, night_of(start), location_id, None)
        cursor.execute("""
            INSERT INTO observations_v4 (id, session_id, start_utc, end_utc, sensor, filter, sensor_temp, sub_exposure,
                                         img_total, notes, image_raw, image_processed, legacy_location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (obs_id, session_id, start, end, sensor, filter_, sensor_temp, sub_exposure, img_total,
              notes or "", image_raw, image_processed, "" if location_id else (location or "")))
        if target_id is not None:
            cursor.execute("""
                INSERT INTO observation_targets (observation_id, target_id, altitude, img_good, img_pass, img_bad)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (obs_id, target_id, altitude or "", img_good or 0, img_pass or 0, img_bad or 0))

    cursor.execute("DROP TABLE observations")
    cursor.execute("ALTER TABLE observations_v4 RENAME TO observations")
    problems = cursor.execute("PRAGMA foreign_key_check").fetchall()
    if problems:
        raise RuntimeError(f"Migration v4 : références incohérentes {problems}")
    cursor.execute("UPDATE schema_version SET version = 4")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON;")


def migrate_to_v5(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT)")
    cursor.execute("""
        CREATE TABLE observation_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            observation_id INTEGER NOT NULL REFERENCES observations (id) ON DELETE CASCADE,
            path TEXT NOT NULL,
            kind TEXT DEFAULT 'traitée',
            software TEXT DEFAULT '',
            palette TEXT DEFAULT '',
            caption TEXT DEFAULT '',
            is_favorite INTEGER DEFAULT 0,
            position INTEGER DEFAULT 0
        );
    """)
    cursor.execute("""
        CREATE TABLE image_targets (
            image_id INTEGER NOT NULL REFERENCES observation_images (id) ON DELETE CASCADE,
            target_id INTEGER NOT NULL REFERENCES targets (id) ON DELETE CASCADE,
            PRIMARY KEY (image_id, target_id)
        );
    """)

    rows = cursor.execute("SELECT id, image_raw, image_processed FROM observations").fetchall()
    for obs_id, raw, processed in rows:
        position = 0
        if processed:
            kind, software, palette, caption = guess_image_details(processed)
            cursor.execute("""
                INSERT INTO observation_images (observation_id, path, kind, software, palette, caption, is_favorite, position)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (obs_id, processed, kind, software, palette, caption, position))
            # L'image traitée montrait la cible de la fiche d'origine (la première de l'observation)
            first_target = cursor.execute(
                "SELECT target_id FROM observation_targets WHERE observation_id = ? ORDER BY rowid LIMIT 1", (obs_id,)
            ).fetchone()
            if first_target:
                cursor.execute("INSERT INTO image_targets (image_id, target_id) VALUES (?, ?)", (cursor.lastrowid, first_target[0]))
            position += 1
        if raw:
            # Le champ « image brute » contenait en pratique la carte de la constellation
            cursor.execute("""
                INSERT INTO observation_images (observation_id, path, kind, is_favorite, position)
                VALUES (?, ?, 'carte', ?, ?)
            """, (obs_id, raw, 0 if processed else 1, position))

    cursor.execute("ALTER TABLE observations DROP COLUMN image_raw")
    cursor.execute("ALTER TABLE observations DROP COLUMN image_processed")
    cursor.execute("UPDATE schema_version SET version = 5")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Table de versionning
    cursor.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
    cursor.execute("SELECT version FROM schema_version")
    row = cursor.fetchone()
    current_version = row[0] if row else 0

    # Sans sauvegarde réussie, l'exception interrompt le démarrage avant toute migration
    if 0 < current_version < LATEST_SCHEMA_VERSION:
        backup_before_migration(current_version)

    if current_version == 0:
        # Initialiser au moment de l'enregistrement de la version
        cursor.execute("INSERT INTO schema_version (version) VALUES (0)")

    # --- VERSION 1: Schéma initial ---
    if current_version < 1:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                usual_name TEXT,
                constellation TEXT,
                other_designations TEXT,
                type TEXT,
                group_name TEXT,
                magnitude TEXT,
                color_index TEXT,
                surf_brightness TEXT,
                size TEXT,
                ra TEXT,
                dec TEXT,
                image_ref TEXT
            );
        """)

        # Table des Observations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                date TEXT NOT NULL,
                obs_start TEXT,
                obs_end TEXT,
                location TEXT,
                altitude TEXT,
                sensor TEXT,
                filter TEXT,
                sensor_temp TEXT,
                sub_exposure TEXT,
                img_total INTEGER,
                img_good INTEGER,
                img_pass INTEGER,
                img_bad INTEGER,
                other_objects TEXT,
                image_raw TEXT,
                image_processed TEXT,
                FOREIGN KEY (target_id) REFERENCES targets (id) ON DELETE CASCADE
            );
        """)
    
        # Injecter des données de test si la base est totalement vide
        cursor.execute("SELECT COUNT(*) FROM targets;")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO targets (name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref)
                VALUES ('M42', 'Nébuleuse d''Orion', 'Ori', 'NGC 1976', 'Nébuleuse en émission', 'Nuage d''Orion', '4.0', '0.0', '11.0', '85'' x 60''', '05h 35m 17s', '-05° 23'' 28"', 'https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=400&q=80');
            """)
            cursor.execute("""
                INSERT INTO targets (name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref)
                VALUES ('M31', 'Galaxie d''Andromède', 'And', 'NGC 224', 'Galaxie spirale', 'Groupe Local', '3.4', '0.6', '13.5', '190'' x 60''', '00h 42m 44s', '+41° 16'' 09"', 'https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=400&q=80');
            """)
            # Observation liée à M42 (id 1)
            cursor.execute("""
                INSERT INTO observations (target_id, date, obs_start, obs_end, location, altitude, sensor, filter, sensor_temp, sub_exposure, img_total, img_good, img_pass, img_bad, other_objects, image_raw, image_processed)
                VALUES (1, '2026-02-15', '21:30', '23:15', 'Jardin - Béthune', '45', 'Seestar S50 (IMX462)', 'IRCUT', '12.5', '10', 150, 120, 10, 20, 'M43, Running Man Nebula (NGC 1977) à proximité immédiate.', 'https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=500&q=80', '');
            """)

        cursor.execute("UPDATE schema_version SET version = 1")
        current_version = 1
        print("Migration vers DB v1 effectuée.")

    # --- VERSION 2: Ajout du champ "notes" ---
    if current_version < 2:
        cursor.execute("ALTER TABLE targets ADD COLUMN notes TEXT DEFAULT '';")
        cursor.execute("UPDATE schema_version SET version = 2")
        current_version = 2
        print("Migration vers DB v2 (ajout des notes) effectuée.")

    # --- VERSION 3: Lieux enregistrés ---
    # Le champ texte "location" est conservé tel quel : il sera converti plus tard (lot Migration)
    if current_version < 3:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                elevation_m REAL,
                bortle REAL,
                notes TEXT DEFAULT ''
            );
        """)
        cursor.execute("ALTER TABLE observations ADD COLUMN location_id INTEGER REFERENCES locations (id) ON DELETE SET NULL;")
        cursor.execute("UPDATE schema_version SET version = 3")
        current_version = 3
        print("Migration vers DB v3 (lieux enregistrés) effectuée.")

    # --- VERSION 4: Sessions, observations multi-cibles, dates complètes ---
    if current_version < 4:
        migrate_to_v4(conn)
        current_version = 4
        print("Migration vers DB v4 (sessions et observations multi-cibles) effectuée.")

    # --- VERSION 5: Images multiples et réglages ---
    if current_version < 5:
        migrate_to_v5(conn)
        current_version = 5
        print("Migration vers DB v5 (images multiples) effectuée.")

    # --- VERSION 6: Relevés météo ---
    if current_version < 6:
        cursor.execute("""
            CREATE TABLE weather_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
                time_utc TEXT NOT NULL,
                cloud_low REAL, cloud_mid REAL, cloud_high REAL,
                seeing_arcsec REAL, index1 REAL, index2 REAL,
                jet_stream_ms REAL, temp_c REAL, humidity_pct REAL, dew_point_c REAL,
                source TEXT NOT NULL DEFAULT 'manuel',
                edited INTEGER NOT NULL DEFAULT 0,
                UNIQUE (session_id, time_utc)
            );
        """)
        cursor.execute("UPDATE schema_version SET version = 6")
        current_version = 6
        print("Migration vers DB v6 (relevés météo) effectuée.")

    # --- VERSION 7: Données à vérifier marquées « c'est normal » ---
    if current_version < 7:
        cursor.execute("""
            CREATE TABLE check_dismissals (
                key TEXT PRIMARY KEY,
                dismissed_at TEXT NOT NULL
            );
        """)
        cursor.execute("UPDATE schema_version SET version = 7")
        current_version = 7
        print("Migration vers DB v7 (données à vérifier) effectuée.")
    conn.commit()
    conn.close()

# Initialisation au démarrage
init_db()

# ================= ENDPOINTS API (FastAPI) =================

@app.get("/api/status")
def get_status():
    return {"status": "ready"}

@app.post("/api/shutdown")
def shutdown_server(background_tasks: BackgroundTasks):
    background_tasks.add_task(self_terminate)
    return {"status": "shutdown scheduled"}

@app.post("/api/export")
def export_database(request: ExportRequest):
    try:
        backup_db(request.path)
    except (OSError, sqlite3.Error) as err:
        raise HTTPException(status_code=500, detail=str(err))
    return {"status": "success"}

@app.get("/api/targets", response_model=List[TargetSchema])
def get_targets():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref, notes FROM targets")
    rows = cursor.fetchall()
    folder = images_folder(conn)
    conn.close()
    
    # On reconstruit les objets JSON pour matcher notre frontend
    return [
        TargetSchema(
            id=r[0], name=r[1], usualName=r[2], constellation=r[3], otherDesignations=r[4],
            type=r[5], group=r[6], magnitude=r[7], colorIndex=r[8], surfBrightness=r[9],
            size=r[10], ra=r[11], dec=r[12], imageRef=to_full_path(r[13] or "", folder), notes=r[14]
        ) for r in rows
    ]

@app.post("/api/targets", response_model=TargetSchema)
def save_target(target: TargetSchema):
    conn = connect()
    cursor = conn.cursor()
    stored_ref = to_stored_path(target.imageRef, images_folder(conn))
    
    if target.id:
        # Mise à jour
        cursor.execute("""
            UPDATE targets SET name=?, usual_name=?, constellation=?, other_designations=?, type=?, group_name=?, magnitude=?, color_index=?, surf_brightness=?, size=?, ra=?, dec=?, image_ref=?, notes=?
            WHERE id=?
        """, (target.name, target.usualName, target.constellation, target.otherDesignations, target.type, target.group, target.magnitude, target.colorIndex, target.surfBrightness, target.size, target.ra, target.dec, stored_ref, target.notes, target.id))
        target_id = target.id
    else:
        # Création
        cursor.execute("""
            INSERT INTO targets (name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (target.name, target.usualName, target.constellation, target.otherDesignations, target.type, target.group, target.magnitude, target.colorIndex, target.surfBrightness, target.size, target.ra, target.dec, stored_ref, target.notes))
        target_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    target.id = target_id
    return target

@app.delete("/api/targets/{target_id}")
def delete_target(target_id: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM targets WHERE id=?", (target_id,))
    # Une observation qui ne vise plus aucune cible disparaît ; celles qui en gardent d'autres restent
    cursor.execute("DELETE FROM observations WHERE id NOT IN (SELECT observation_id FROM observation_targets)")
    delete_empty_sessions(cursor)
    conn.commit()
    conn.close()
    return {"status": "success"}

OBSERVATION_COLUMNS = """
    o.id, o.start_utc, o.end_utc, s.location_id, s.bortle, o.session_id, s.night_date, o.instrument, o.sensor,
    o.filter, o.sensor_temp, o.sub_exposure, o.img_total, o.notes, o.legacy_location
"""

def observation_from_row(r, targets, images) -> ObservationSchema:
    return ObservationSchema(
        id=r[0], start=r[1], end=r[2] or "", locationId=r[3], bortle=r[4], sessionId=r[5], nightDate=r[6] or "",
        instrument=r[7] or "", sensor=r[8] or "", filter=r[9] or "", sensorTemp=r[10] or "", subExposure=r[11] or "",
        imgTotal=r[12] or 0, notes=r[13] or "", legacyLocation=r[14] or "", targets=targets, images=images,
    )

def read_observations(conn, observation_id: Optional[int] = None) -> List[ObservationSchema]:
    where = "WHERE o.id = ?" if observation_id is not None else ""
    params = (observation_id,) if observation_id is not None else ()
    rows = conn.execute(f"SELECT {OBSERVATION_COLUMNS} FROM observations o LEFT JOIN sessions s ON s.id = o.session_id {where}", params).fetchall()
    targets = {}
    for t in conn.execute("SELECT observation_id, target_id, altitude, img_good, img_pass, img_bad, notes FROM observation_targets ORDER BY rowid"):
        targets.setdefault(t[0], []).append(ObservationTargetSchema(
            targetId=t[1], altitude=t[2] or "", imgGood=t[3] or 0, imgPass=t[4] or 0, imgBad=t[5] or 0, notes=t[6] or "",
        ))
    images = read_images(conn)
    return [observation_from_row(r, targets.get(r[0], []), images.get(r[0], [])) for r in rows]

def read_images(conn):
    folder = images_folder(conn)
    image_targets = {}
    for image_id, target_id in conn.execute("SELECT image_id, target_id FROM image_targets ORDER BY rowid"):
        image_targets.setdefault(image_id, []).append(target_id)
    images = {}
    for i in conn.execute("""
        SELECT id, observation_id, path, kind, software, palette, caption, is_favorite
        FROM observation_images ORDER BY observation_id, position, id
    """):
        full = to_full_path(i[2], folder)
        images.setdefault(i[1], []).append(ObservationImageSchema(
            id=i[0], path=full, kind=i[3] or "", software=i[4] or "", palette=i[5] or "", caption=i[6] or "",
            isFavorite=bool(i[7]), targetIds=image_targets.get(i[0], []), missing=file_missing(full),
        ))
    return images

def save_images(cursor, observation_id: int, images: List[ObservationImageSchema], folder: str):
    """Remplace les images de l'observation par la liste reçue, dans cet ordre."""
    kept = [i.id for i in images if i.id]
    cursor.execute(
        f"DELETE FROM observation_images WHERE observation_id = ? AND id NOT IN ({','.join('?' * len(kept)) or 'NULL'})",
        (observation_id, *kept),
    )
    # Une seule image favorite : la première cochée, sinon la première de la liste
    favorite = next((n for n, i in enumerate(images) if i.isFavorite), 0)
    for position, image in enumerate(images):
        values = (to_stored_path(image.path, folder), image.kind, image.software, image.palette, image.caption,
                  int(position == favorite), position)
        cursor.execute("UPDATE observation_images SET path=?, kind=?, software=?, palette=?, caption=?, is_favorite=?, position=? WHERE id=? AND observation_id=?",
                       (*values, image.id, observation_id))
        if not image.id or cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO observation_images (path, kind, software, palette, caption, is_favorite, position, observation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (*values, observation_id))
            image.id = cursor.lastrowid
        cursor.execute("DELETE FROM image_targets WHERE image_id = ?", (image.id,))
        for target_id in dict.fromkeys(image.targetIds):
            cursor.execute("INSERT INTO image_targets (image_id, target_id) VALUES (?, ?)", (image.id, target_id))

@app.get("/api/observations", response_model=List[ObservationSchema])
def get_observations():
    conn = connect()
    observations = read_observations(conn)
    conn.close()
    return observations

@app.post("/api/observations", response_model=ObservationSchema)
def save_observation(obs: ObservationSchema):
    obs.start = obs.start.strip().replace("T", " ")
    obs.end = obs.end.strip().replace("T", " ")
    if not DATETIME_PATTERN.match(obs.start):
        raise HTTPException(status_code=422, detail="Le début de l'observation (date et heure TU) est obligatoire.")
    if obs.end and not DATETIME_PATTERN.match(obs.end):
        raise HTTPException(status_code=422, detail="La fin de l'observation n'est pas une date et heure valides.")
    if obs.end and obs.end < obs.start:
        raise HTTPException(status_code=422, detail="La fin de l'observation précède son début.")
    target_ids = [t.targetId for t in obs.targets]
    if not target_ids:
        raise HTTPException(status_code=422, detail="Ajoutez au moins une cible à l'observation.")
    if len(set(target_ids)) != len(target_ids):
        raise HTTPException(status_code=422, detail="Une même cible apparaît deux fois.")

    if obs.id and obs.id > 1000000000: # Détecte un ID temporaire JS (timestamp) pour forcer la création
        obs.id = None

    conn = connect()
    cursor = conn.cursor()
    try:
        session_id = find_or_create_session(cursor, night_of(obs.start), obs.locationId, obs.bortle)
        values = (session_id, obs.start, obs.end, obs.instrument, obs.sensor, obs.filter, obs.sensorTemp, obs.subExposure,
                  obs.imgTotal, obs.notes)
        if obs.id:
            cursor.execute("""
                UPDATE observations SET session_id=?, start_utc=?, end_utc=?, instrument=?, sensor=?, filter=?, sensor_temp=?,
                       sub_exposure=?, img_total=?, notes=?
                WHERE id=?
            """, (*values, obs.id))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Observation introuvable.")
            cursor.execute("DELETE FROM observation_targets WHERE observation_id=?", (obs.id,))
            # Un lieu enregistré remplace l'ancienne saisie en texte libre
            if obs.locationId is not None:
                cursor.execute("UPDATE observations SET legacy_location='' WHERE id=?", (obs.id,))
        else:
            cursor.execute("""
                INSERT INTO observations (session_id, start_utc, end_utc, instrument, sensor, filter, sensor_temp,
                                          sub_exposure, img_total, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
            obs.id = cursor.lastrowid
        for t in obs.targets:
            cursor.execute("""
                INSERT INTO observation_targets (observation_id, target_id, altitude, img_good, img_pass, img_bad, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (obs.id, t.targetId, t.altitude, t.imgGood, t.imgPass, t.imgBad, t.notes))
        # Une image ne peut montrer qu'une cible de l'observation
        for image in obs.images:
            image.targetIds = [t for t in image.targetIds if t in target_ids]
        save_images(cursor, obs.id, obs.images, images_folder(conn))
        delete_empty_sessions(cursor)
        conn.commit()
        return read_observations(conn, obs.id)[0]
    except sqlite3.IntegrityError as err:
        raise HTTPException(status_code=422, detail=f"Cible inconnue ou donnée incohérente : {err}")
    finally:
        conn.close()

@app.delete("/api/observations/{obs_id}")
def delete_observation(obs_id: int):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM observations WHERE id=?", (obs_id,))
    delete_empty_sessions(cursor)
    conn.commit()
    conn.close()
    return {"status": "success"}

# ================= RÉGLAGES =================
@app.get("/api/settings", response_model=SettingsSchema)
def get_settings():
    conn = connect()
    settings = SettingsSchema(imagesFolder=images_folder(conn), weatherMarginHours=weather_margin(conn))
    conn.close()
    return settings

@app.post("/api/settings", response_model=SettingsSchema)
def save_settings(settings: SettingsSchema):
    folder = settings.imagesFolder.strip()
    if folder and not os.path.isabs(folder):
        raise HTTPException(status_code=422, detail="Le dossier des images doit être un chemin complet (ex. E:\\Astro).")
    if not 0 <= settings.weatherMarginHours <= 6:
        raise HTTPException(status_code=422, detail="La marge météo doit être comprise entre 0 et 6 heures.")
    conn = connect()
    cursor = conn.cursor()
    previous = images_folder(conn)
    write_setting(cursor, "images_folder", folder)
    write_setting(cursor, "weather_margin_hours", str(settings.weatherMarginHours))
    # Les chemins déjà relatifs suivent le nouveau dossier (changement de lettre de disque) ;
    # les chemins complets qui se trouvent dans ce dossier deviennent relatifs.
    # Sans dossier, les chemins relatifs redeviennent complets d'après l'ancien dossier.
    def convert(path: str) -> str:
        return to_stored_path(path, folder) if folder else to_full_path(path, previous)
    for image_id, path in cursor.execute("SELECT id, path FROM observation_images").fetchall():
        cursor.execute("UPDATE observation_images SET path = ? WHERE id = ?", (convert(path), image_id))
    for target_id, path in cursor.execute("SELECT id, image_ref FROM targets").fetchall():
        cursor.execute("UPDATE targets SET image_ref = ? WHERE id = ?", (convert(path or ""), target_id))
    conn.commit()
    conn.close()
    return SettingsSchema(imagesFolder=folder, weatherMarginHours=settings.weatherMarginHours)


# ================= LIEUX =================
def location_from_row(r) -> LocationSchema:
    return LocationSchema(id=r[0], label=r[1], lat=r[2], lon=r[3], elevationM=r[4], bortle=r[5], notes=r[6] or "")

@app.get("/api/locations", response_model=List[LocationSchema])
def get_locations():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, label, lat, lon, elevation_m, bortle, notes FROM locations ORDER BY label COLLATE NOCASE").fetchall()
    conn.close()
    return [location_from_row(r) for r in rows]

@app.post("/api/locations", response_model=LocationSchema)
def save_location(location: LocationSchema):
    label = location.label.strip()
    if not label:
        raise HTTPException(status_code=422, detail="Le libellé du lieu est obligatoire.")
    if not (-90 <= location.lat <= 90 and -180 <= location.lon <= 180):
        raise HTTPException(status_code=422, detail="Coordonnées hors limites.")
    location.label = label

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    values = (location.label, location.lat, location.lon, location.elevationM, location.bortle, location.notes)
    if location.id:
        cursor.execute("UPDATE locations SET label=?, lat=?, lon=?, elevation_m=?, bortle=?, notes=? WHERE id=?", (*values, location.id))
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Lieu introuvable.")
    else:
        cursor.execute("INSERT INTO locations (label, lat, lon, elevation_m, bortle, notes) VALUES (?, ?, ?, ?, ?, ?)", values)
        location.id = cursor.lastrowid
    conn.commit()
    conn.close()
    return location


# ================= SERVICES EN LIGNE (carte des lieux) =================
# Nominatim exige un User-Agent qui identifie l'application : les appels passent donc par le backend
USER_AGENT = "AllNightLong (+https://github.com/dchatel/allnightlong)"
EXTERNAL_TIMEOUT_S = 10
# Certificats vérifiés par le système, comme le navigateur : le magasin lu par Python peut
# contenir des certificats intermédiaires expirés qui font échouer certains sites
SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

def fetch_json(url: str, params: dict):
    request = urllib.request.Request(
        f"{url}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "fr"},
    )
    try:
        with urllib.request.urlopen(request, timeout=EXTERNAL_TIMEOUT_S, context=SSL_CONTEXT) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, ValueError) as err:
        raise HTTPException(status_code=502, detail=f"Service en ligne injoignable : {err}")

# Nom de commune le plus précis disponible, proposé comme libellé du lieu
def place_name(address: dict) -> str:
    for key in ("village", "town", "city", "hamlet", "municipality", "suburb", "county"):
        if address.get(key):
            return address[key]
    return ""

@app.get("/api/geo/reverse")
def reverse_geocode(lat: float, lon: float):
    data = fetch_json("https://nominatim.openstreetmap.org/reverse", {
        "format": "jsonv2", "lat": lat, "lon": lon, "zoom": 18, "addressdetails": 1,
    })
    return {"address": data.get("display_name", ""), "place": place_name(data.get("address", {}))}

@app.get("/api/geo/search")
def search_place(q: str):
    data = fetch_json("https://nominatim.openstreetmap.org/search", {
        "format": "jsonv2", "q": q, "limit": 5,
    })
    return [{"address": d.get("display_name", ""), "lat": float(d["lat"]), "lon": float(d["lon"])} for d in data]

@app.get("/api/geo/elevation")
def get_elevation(lat: float, lon: float):
    data = fetch_json("https://api.open-meteo.com/v1/elevation", {"latitude": lat, "longitude": lon})
    elevations = data.get("elevation") or [None]
    return {"elevationM": elevations[0]}


# ================= MÉTÉO (Open-Meteo) =================
WEATHER_COLUMNS = ("cloud_low", "cloud_mid", "cloud_high", "seeing_arcsec", "index1", "index2",
                   "jet_stream_ms", "temp_c", "humidity_pct", "dew_point_c")
WEATHER_FIELDS = ("cloudLow", "cloudMid", "cloudHigh", "seeing", "index1", "index2",
                  "jetStream", "temp", "humidity", "dewPoint")
# Variables Open-Meteo → colonnes (le seeing et les index sont propres à meteoblue)
OPEN_METEO_VARIABLES = {
    "cloud_cover_low": "cloud_low", "cloud_cover_mid": "cloud_mid", "cloud_cover_high": "cloud_high",
    "temperature_2m": "temp_c", "relative_humidity_2m": "humidity_pct", "dew_point_2m": "dew_point_c",
    "wind_speed_250hPa": "jet_stream_ms",
}
# Au-delà de quelques jours, les prévisions archivées remplacent l'API de prévision
RECENT_DAYS = 5

def read_weather(conn, session_id: int) -> List[WeatherReadingSchema]:
    rows = conn.execute(f"""
        SELECT time_utc, {', '.join(WEATHER_COLUMNS)}, source, edited
        FROM weather_readings WHERE session_id = ? ORDER BY time_utc
    """, (session_id,)).fetchall()
    return [WeatherReadingSchema(time=r[0], **dict(zip(WEATHER_FIELDS, r[1:11])), source=r[11], edited=bool(r[12])) for r in rows]

def session_point(conn, session_id: int):
    """Coordonnées de la session : celles du lieu enregistré, sinon l'ancienne saisie en texte libre."""
    row = conn.execute("""
        SELECT l.lat, l.lon FROM sessions s JOIN locations l ON l.id = s.location_id WHERE s.id = ?
    """, (session_id,)).fetchone()
    if row:
        return row
    for (legacy,) in conn.execute("SELECT legacy_location FROM observations WHERE session_id = ?", (session_id,)):
        numbers = re.findall(r"-?\d+[.,]\d+", legacy or "")
        if len(numbers) >= 2:
            lat, lon = (float(n.replace(",", ".")) for n in numbers[:2])
            if abs(lat) <= 90 and abs(lon) <= 180:
                return lat, lon
    return None

def session_window(conn, session_id: int):
    """Créneau des observations de la session, élargi de la marge réglée, en heures pleines TU."""
    margin = timedelta(hours=weather_margin(conn))
    starts, ends = [], []
    for start, end in conn.execute("SELECT start_utc, end_utc FROM observations WHERE session_id = ?", (session_id,)):
        if len(start) > 10:
            starts.append(datetime.strptime(start, "%Y-%m-%d %H:%M"))
            ends.append(datetime.strptime(end, "%Y-%m-%d %H:%M") if end and len(end) > 10 else starts[-1])
        else:
            # Heure inconnue : toute la nuit, de 16 h à 8 h TU
            day = datetime.strptime(start, "%Y-%m-%d")
            starts.append(day + timedelta(hours=16))
            ends.append(day + timedelta(hours=32))
    if not starts:
        return None
    first = (min(starts) - margin).replace(minute=0)
    last = max(ends) + margin
    if last.minute:
        last = last.replace(minute=0) + timedelta(hours=1)
    return first, last

def fetch_open_meteo(lat: float, lon: float, first: datetime, last: datetime) -> dict:
    """Relevés horaires Open-Meteo entre deux heures TU : {"AAAA-MM-JJ HH:MM": {colonne: valeur}}."""
    recent = last >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=RECENT_DAYS)
    host = "https://api.open-meteo.com" if recent else "https://historical-forecast-api.open-meteo.com"
    data = fetch_json(f"{host}/v1/forecast", {
        "latitude": lat, "longitude": lon, "hourly": ",".join(OPEN_METEO_VARIABLES),
        "wind_speed_unit": "ms", "timezone": "GMT",
        "start_date": f"{first:%Y-%m-%d}", "end_date": f"{last:%Y-%m-%d}",
    })
    if data.get("error"):
        raise HTTPException(status_code=502, detail=f"Open-Meteo : {data.get('reason', 'erreur')}")
    hourly = data.get("hourly", {})
    readings = {}
    for n, stamp in enumerate(hourly.get("time", [])):
        moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M")
        if first <= moment <= last:
            readings[f"{moment:%Y-%m-%d %H:%M}"] = {column: hourly.get(variable, [None] * (n + 1))[n]
                                                     for variable, column in OPEN_METEO_VARIABLES.items()}
    return readings

@app.get("/api/sessions/{session_id}/weather", response_model=List[WeatherReadingSchema])
def get_weather(session_id: int):
    conn = connect()
    readings = read_weather(conn, session_id)
    conn.close()
    return readings

@app.post("/api/sessions/{session_id}/weather/fetch", response_model=List[WeatherReadingSchema])
def fetch_weather(session_id: int, refresh: bool = False):
    """Récupère la météo Open-Meteo sur le créneau de la session.
    Sans "refresh", seules les heures manquantes sont ajoutées ; avec, les relevés Open-Meteo non modifiés
    sont aussi mis à jour. Les relevés saisis ou corrigés par l'utilisateur ne sont jamais écrasés."""
    conn = connect()
    try:
        point = session_point(conn, session_id)
        window = session_window(conn, session_id)
        if not point:
            raise HTTPException(status_code=422, detail="Choisissez un lieu pour récupérer la météo.")
        if not window:
            raise HTTPException(status_code=404, detail="Session introuvable.")
        existing = {r.time: r for r in read_weather(conn, session_id)}
        if not refresh and all(t in existing for t in hours_between(*window)):
            return list(existing.values())
        fetched = fetch_open_meteo(*point, *window)
        cursor = conn.cursor()
        for time, values in fetched.items():
            current = existing.get(time)
            if current and (current.source != "open-meteo" or current.edited or not refresh):
                continue
            columns = list(values)
            cursor.execute(f"""
                INSERT INTO weather_readings (session_id, time_utc, {', '.join(columns)}, source, edited)
                VALUES (?, ?, {', '.join('?' * len(columns))}, 'open-meteo', 0)
                ON CONFLICT (session_id, time_utc) DO UPDATE SET {', '.join(f'{c} = excluded.{c}' for c in columns)}
            """, (session_id, time, *values.values()))
        conn.commit()
        return read_weather(conn, session_id)
    finally:
        conn.close()

def hours_between(first: datetime, last: datetime):
    moment = first
    while moment <= last:
        yield f"{moment:%Y-%m-%d %H:%M}"
        moment += timedelta(hours=1)

# Ligne meteoblue telle que saisie dans les notes :
#   « 21h00 TU ( 34-0-0 / 1.39 / 4-2 / 16ms / 13°C / 91% ) »
# nuages bas-moyens-hauts / seeing / index 1-2 / jet stream / température / humidité.
METEOBLUE_VALUES = re.compile(
    r"\(\s*(\d+)\s*[-_]\s*(\d+)\s*[-_]\s*(\d+)\s*/\s*([\d.,]+|\?+)\s*/\s*(\d+)\s*[-_]\s*(\d+)\s*/"
    r"\s*([\d.,]+)\s*m\s*/?\s*s\s*/\s*(-?[\d.,]+)\s*°?\s*C?\s*/\s*(\d+|\?+)\s*%?\s*\)",
    re.IGNORECASE,
)
METEOBLUE_TIME = re.compile(r"\b(\d{1,2})\s*h\s*(\d{2})?|\b([01]\d|2[0-3])([0-5]\d)\b")

def dew_point(temp: Optional[float], humidity: Optional[float]) -> Optional[float]:
    """Point de rosée (formule de Magnus) : meteoblue ne le donne pas, la température et l'humidité suffisent."""
    if temp is None or not humidity:
        return None
    gamma = math.log(humidity / 100) + 17.62 * temp / (243.12 + temp)
    return round(243.12 * gamma / (17.62 - gamma), 1)

def meteoblue_number(text: str) -> Optional[float]:
    return None if "?" in text else float(text.replace(",", "."))

def parse_meteoblue(text: str, night_date: str) -> List[WeatherReadingSchema]:
    """Relevés trouvés dans un texte. L'heure est la première écrite avant la parenthèse ;
    avant midi, elle appartient au lendemain de la nuit."""
    night = datetime.strptime(night_date, "%Y-%m-%d")
    readings = {}
    for line in text.splitlines():
        values = METEOBLUE_VALUES.search(line)
        time = METEOBLUE_TIME.search(line[: values.start()]) if values else None
        if not values or not time:
            continue
        hour = int(time.group(1) or time.group(3))
        minute = int(time.group(2) or time.group(4) or 0)
        if hour > 23 or minute > 59:
            continue
        moment = night.replace(hour=hour, minute=minute) + timedelta(days=0 if hour >= 12 else 1)
        low, mid, high, seeing, index1, index2, jet, temp, humidity = values.groups()
        stamp = f"{moment:%Y-%m-%d %H:%M}"
        readings[stamp] = WeatherReadingSchema(
            time=stamp, cloudLow=float(low), cloudMid=float(mid), cloudHigh=float(high),
            seeing=meteoblue_number(seeing), index1=float(index1), index2=float(index2),
            jetStream=meteoblue_number(jet), temp=meteoblue_number(temp), humidity=meteoblue_number(humidity),
            dewPoint=dew_point(meteoblue_number(temp), meteoblue_number(humidity)),
            source="meteoblue", edited=True,
        )
    return sorted(readings.values(), key=lambda r: r.time)

class MeteoblueParseRequest(BaseModel):
    text: str
    nightDate: str

@app.post("/api/weather/parse-meteoblue", response_model=List[WeatherReadingSchema])
def parse_meteoblue_text(request: MeteoblueParseRequest):
    try:
        datetime.strptime(request.nightDate, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Date de nuit invalide.")
    return parse_meteoblue(request.text, request.nightDate)

@app.post("/api/sessions/{session_id}/weather/readings", response_model=List[WeatherReadingSchema])
def save_weather(session_id: int, readings: List[WeatherReadingSchema]):
    """Remplace les relevés de la session (grille météo modifiée par l'utilisateur)."""
    times = [r.time.replace("T", " ") for r in readings]
    if len(set(times)) != len(times):
        raise HTTPException(status_code=422, detail="Deux relevés ont la même heure.")
    if any(not DATETIME_PATTERN.match(t) or len(t) <= 10 for t in times):
        raise HTTPException(status_code=422, detail="Chaque relevé doit avoir une date et une heure TU.")
    conn = connect()
    cursor = conn.cursor()
    if not cursor.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Session introuvable.")
    cursor.execute("DELETE FROM weather_readings WHERE session_id = ?", (session_id,))
    for time, r in zip(times, readings):
        cursor.execute(f"""
            INSERT INTO weather_readings (session_id, time_utc, {', '.join(WEATHER_COLUMNS)}, source, edited)
            VALUES (?, ?, {', '.join('?' * len(WEATHER_COLUMNS))}, ?, ?)
        """, (session_id, time, *(getattr(r, f) for f in WEATHER_FIELDS), r.source, int(r.edited)))
    conn.commit()
    readings = read_weather(conn, session_id)
    conn.close()
    return readings


# ================= PRÉ-REMPLISSAGE DEPUIS UN FITS =================
class FitsRequest(BaseModel):
    path: str

# Lieu enregistré qui correspond aux coordonnées du Seestar, à cette distance près
FITS_LOCATION_RADIUS_M = 300

@app.post("/api/fits/read")
def read_fits(request: FitsRequest):
    """Résumé d'une capture à partir d'un FITS du Seestar, avec la cible et le lieu retrouvés dans la base."""
    path = Path(request.path)
    if path.suffix.lower() not in fits.FITS_SUFFIXES or not path.is_file():
        raise HTTPException(status_code=422, detail="Choisissez un fichier FITS (.fit) du Seestar.")
    try:
        summary = fits.capture_summary(path)
    except (OSError, ValueError, KeyError) as err:
        raise HTTPException(status_code=422, detail=f"FITS illisible : {err}")

    conn = connect()
    # Cibles : l'objet de l'en-tête, puis toutes les désignations citées dans le nom du dossier
    # (« NGC 147 - NGC 185 »). L'objet vient en premier ; « Unknown » ou une étoile guide ne trouvent rien.
    wanted = [fits.normalize_name(summary["object"])] + sorted(fits.name_tokens(summary["folder"]))
    by_name = {fits.normalize_name(name): tid for tid, name in conn.execute("SELECT id, name FROM targets")}
    summary["targetIds"] = list(dict.fromkeys(by_name[w] for w in wanted if w in by_name))
    summary["locationId"] = None
    if summary["lat"] is not None and summary["lon"] is not None:
        best = None
        for lid, lat, lon in conn.execute("SELECT id, lat, lon FROM locations"):
            metres = math.hypot((lat - summary["lat"]) * 111_320,
                                (lon - summary["lon"]) * 111_320 * math.cos(math.radians(lat)))
            if metres <= FITS_LOCATION_RADIUS_M and (best is None or metres < best[0]):
                best = (metres, lid)
        summary["locationId"] = best[1] if best else None
    conn.close()
    return summary


# ================= DONNÉES À VÉRIFIER =================
# Les contrôles sont calculés par l'interface (ils ont besoin des éphémérides) ; la base retient seulement
# les signalements que l'utilisateur a marqués « c'est normal », par une clé stable.
class CheckDismissal(BaseModel):
    key: str
    dismissed: bool = True

@app.get("/api/checks/dismissed", response_model=List[str])
def get_dismissed_checks():
    conn = connect()
    keys = [k for (k,) in conn.execute("SELECT key FROM check_dismissals ORDER BY key")]
    conn.close()
    return keys

@app.post("/api/checks/dismissed", response_model=List[str])
def set_dismissed_check(dismissal: CheckDismissal):
    conn = connect()
    if dismissal.dismissed:
        conn.execute("INSERT OR IGNORE INTO check_dismissals (key, dismissed_at) VALUES (?, ?)",
                     (dismissal.key, datetime.now().strftime("%Y-%m-%d %H:%M")))
    else:
        conn.execute("DELETE FROM check_dismissals WHERE key = ?", (dismissal.key,))
    conn.commit()
    conn.close()
    return get_dismissed_checks()

# Tous les relevés, pour repérer un même relevé recopié sur deux nuits
class SessionWeatherReading(WeatherReadingSchema):
    sessionId: int

@app.get("/api/weather", response_model=List[SessionWeatherReading])
def get_all_weather():
    conn = connect()
    rows = conn.execute(f"""
        SELECT session_id, time_utc, {', '.join(WEATHER_COLUMNS)}, source, edited FROM weather_readings ORDER BY session_id, time_utc
    """).fetchall()
    conn.close()
    return [SessionWeatherReading(sessionId=r[0], time=r[1], **dict(zip(WEATHER_FIELDS, r[2:12])), source=r[12], edited=bool(r[13]))
            for r in rows]


if __name__ == "__main__":
    import uvicorn

    if IS_SIDECAR:
        threading.Thread(target=exit_when_parent_dies, daemon=True).start()

        # Port libre choisi par le système et communiqué à l'application via stdout
        server_socket = socket.socket()
        server_socket.bind(("127.0.0.1", 0))
        print(f"ALLNIGHTLONG_PORT={server_socket.getsockname()[1]}", flush=True)
        uvicorn.Server(uvicorn.Config(app)).run(sockets=[server_socket])
    else:
        # Développement : démarre le serveur web FastAPI sur le port 8000
        uvicorn.run(app, host="127.0.0.1", port=8000)