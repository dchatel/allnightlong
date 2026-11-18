"""Reprise des observations existantes (lot 6 du document de conception).

Ce script travaille TOUJOURS sur une copie : il lit la base d'origine, la copie dans un dossier de
travail, amène la copie au schéma courant (migrations de l'application), puis :

  1. lit l'en-tête de la première et de la dernière pose de chaque capture Seestar (FITS) ;
  2. associe chaque observation à sa capture (heure de début, nom de la cible, date) ;
  3. reprend le début et la fin exacts (DATE-OBS, en TU) ;
  4. fusionne les fiches d'une même capture en une observation à plusieurs cibles ;
  5. crée le lieu « Jardin » à partir des coordonnées enregistrées par le Seestar ;
  6. reprend le Bortle et les relevés meteoblue écrits dans les notes ;
  7. complète la météo avec Open-Meteo (facultatif) ;
  8. écrit un compte rendu à faire valider avant de livrer la base.

Usage :
  python -I tools/migrate_observations.py SOURCE.db --fits "L:\\Images_astro (Seestar)\\Capture" --out DOSSIER [--open-meteo]

Les décisions prises à la main (fiche sans capture évidente…) sont dans migration_overrides.json.
"""
import argparse
import json
import math
import os
import re
import shutil
import sqlite3
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIGRATION_KEY = "lot6_migration"
# Une heure de début saisie à la main peut s'écarter de celle des FITS (heure locale, faute de frappe)
TIME_TOLERANCE_MIN = 75
# Coordonnées regroupées dans un même lieu en dessous de cette distance
LOCATION_RADIUS_M = 150


# ---------------------------------------------------------------- FITS
def fits_header(path: Path) -> dict:
    """Mots-clés de l'en-tête FITS (blocs de 2880 octets, cartes de 80 caractères)."""
    cards = {}
    with open(path, "rb") as f:
        while True:
            block = f.read(2880)
            if len(block) < 2880:
                return cards
            for i in range(0, 2880, 80):
                card = block[i:i + 80].decode("ascii", "replace")
                key = card[:8].strip()
                if key == "END":
                    return cards
                if card[8:10] == "= ":
                    cards[key] = card[10:].split(" /")[0].strip().strip("'").strip()


def parse_fits_date(value: str) -> datetime:
    return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")


def read_captures(root: Path) -> list:
    """Une capture = un dossier « <cible>_sub » de poses « Light_… » dans un dossier de nuit."""
    captures = []
    for night_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for sub_dir in sorted(p for p in night_dir.iterdir() if p.is_dir() and p.name.endswith("_sub")):
            lights = sorted(
                (p for p in sub_dir.rglob("Light*") if p.suffix.lower() in (".fit", ".fits")),
                key=lambda p: p.stem.rsplit("_", 1)[-1],
            )
            if not lights:
                continue
            first, last = fits_header(lights[0]), fits_header(lights[-1])
            exposure = float(first.get("EXPTIME") or 0)
            stack_dir = night_dir / sub_dir.name[:-4]
            stacked = [int(m.group(1)) for f in (stack_dir.iterdir() if stack_dir.is_dir() else [])
                       for m in [re.match(r"Stacked_(\d+)_", f.name)] if m]
            captures.append({
                "key": f"{night_dir.name}/{sub_dir.name[:-4]}",
                "names": f"{night_dir.name} {sub_dir.name} {first.get('OBJECT', '')}",
                "start": parse_fits_date(first["DATE-OBS"]),
                "end": parse_fits_date(last["DATE-OBS"]) + timedelta(seconds=exposure),
                "lights": len(lights),
                "stacked": max(stacked) if stacked else None,
                "exposure": exposure,
                "filters": sorted({p.stem.split("_")[-2] for p in lights}),
                "sensor_temp": first.get("CCD-TEMP"),
                "lat": float(first["SITELAT"]) if first.get("SITELAT") else None,
                "lon": float(first["SITELONG"]) if first.get("SITELONG") else None,
            })
    return captures


# ---------------------------------------------------------------- Correspondances
def normalize(name: str) -> str:
    """« M42 », « M 42 », « m_42 » → « m42 » ; idem pour NGC, IC, Sh2…"""
    return re.sub(r"[\s_\-.]", "", name.lower())


def name_tokens(text: str) -> set:
    tokens = set()
    for m in re.finditer(r"\b(m|ngc|ic|sh2|c|hip)[\s_]*-?\s*(\d+[a-z]?)", text.lower()):
        tokens.add(m.group(1) + m.group(2))
    # « NGC 4631,4627 » ou « NGC 6992,6995 » : numéros qui suivent un catalogue déjà cité
    for m in re.finditer(r"\b(ngc|ic)[\s_]*(\d+(?:\s*[,/-]\s*\d+)+)", text.lower()):
        for number in re.findall(r"\d+", m.group(2)):
            tokens.add(m.group(1) + number)
    return tokens


def match_capture(obs: dict, captures: list):
    """Meilleure capture pour une observation, avec la raison du choix (ou None)."""
    date = datetime.strptime(obs["start"][:10], "%Y-%m-%d")
    has_time = len(obs["start"]) > 10
    target_keys = {normalize(n) for n in obs["target_names"]}
    best = None
    for c in captures:
        day_gap = (c["start"].date() - date.date()).days
        if not -2 <= day_gap <= 1:
            continue
        named = bool(target_keys & name_tokens(c["names"]))
        if has_time:
            entered = datetime.strptime(obs["start"][11:16], "%H:%M")
            minutes = abs((c["start"].hour * 60 + c["start"].minute) - (entered.hour * 60 + entered.minute))
            minutes = min(minutes, 1440 - minutes)
            if minutes > TIME_TOLERANCE_MIN or (minutes > 10 and not named):
                continue
        else:
            if not named:
                continue
            minutes = 0
        score = (0 if named else 500) + minutes + abs(day_gap) * 5
        if best is None or score < best[0]:
            best = (score, c, named, minutes)
    if not best:
        return None, None
    _, capture, named, minutes = best
    # Seules les correspondances qui méritent un coup d'œil sont expliquées
    notes = [] if named else ["reconnue par l'heure seule"]
    if minutes > 5:
        notes.append(f"heure saisie décalée de {minutes} min")
    return capture, ", ".join(notes)


# ---------------------------------------------------------------- Notes
BORTLE = re.compile(r"bortle\s*:?\s*(\d+(?:[.,]\d)?)", re.IGNORECASE)


def bortle_from_notes(text: str):
    m = BORTLE.search(text or "")
    return float(m.group(1).replace(",", ".")) if m else None


# ---------------------------------------------------------------- Lieux
def distance_m(a, b) -> float:
    lat = math.radians((a[0] + b[0]) / 2)
    return math.hypot((a[0] - b[0]) * 111_320, (a[1] - b[1]) * 111_320 * math.cos(lat))


# ---------------------------------------------------------------- Migration
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path, help="base d'origine (jamais modifiée)")
    parser.add_argument("--fits", type=Path, required=True, help="dossier « Capture » des FITS du Seestar")
    parser.add_argument("--out", type=Path, required=True, help="dossier de travail (copie migrée + compte rendu)")
    parser.add_argument("--open-meteo", action="store_true", help="compléter la météo avec Open-Meteo")
    args = parser.parse_args()

    overrides_path = Path(__file__).with_name("migration_overrides.json")
    overrides = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}

    # Copie de travail, amenée au schéma courant par les migrations de l'application
    work = args.out / "allnightlong"
    work.mkdir(parents=True, exist_ok=True)
    db_path = work / "allnightlong.db"
    shutil.copy2(args.source, db_path)
    os.environ["APPDATA"] = str(args.out)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import main as app  # noqa: E402  (exécute init_db sur la copie)

    conn = app.connect()
    cursor = conn.cursor()
    if app.read_setting(conn, MIGRATION_KEY):
        sys.exit("Cette base a déjà été reprise (réglage « lot6_migration »).")

    report = Report()
    captures = read_captures(args.fits)
    by_key = {c["key"]: c for c in captures}
    report.line(f"Base d'origine : `{args.source}`  ")
    report.line(f"Captures FITS lues : {len(captures)} (dossier `{args.fits}`)\n")

    # --- Observations et cibles
    observations = []
    for obs_id, start, end, notes, total in cursor.execute(
            "SELECT id, start_utc, end_utc, notes, img_total FROM observations ORDER BY start_utc"):
        names = [n for (n,) in conn.execute("""
            SELECT t.name FROM observation_targets ot JOIN targets t ON t.id = ot.target_id
            WHERE ot.observation_id = ? ORDER BY ot.rowid""", (obs_id,))]
        observations.append({"id": obs_id, "start": start, "end": end, "notes": notes or "", "total": total,
                             "target_names": names})

    # --- 1-2. Correspondance avec les captures
    groups = {}
    unmatched = []
    for obs in observations:
        forced = overrides.get("observations", {}).get(str(obs["id"]))
        if forced:
            capture, reason = by_key.get(forced["capture"]), f"décision manuelle : {forced['reason']}"
            if capture is None:
                sys.exit(f"Capture inconnue dans migration_overrides.json : {forced['capture']}")
        else:
            capture, reason = match_capture(obs, captures)
        if capture is None:
            unmatched.append(obs)
            continue
        obs["reason"] = reason
        groups.setdefault(capture["key"], []).append(obs)

    # --- 5. Lieu « Jardin » : coordonnées du Seestar regroupées
    points = [(c["lat"], c["lon"]) for c in captures if c["lat"] is not None and c["key"] in groups]
    center = (statistics.median(p[0] for p in points), statistics.median(p[1] for p in points))
    far = [(c["key"], round(distance_m(center, (c["lat"], c["lon"])))) for c in captures
           if c["key"] in groups and c["lat"] is not None and distance_m(center, (c["lat"], c["lon"])) > LOCATION_RADIUS_M]
    bortles = [b for o in observations if (b := bortle_from_notes(o["notes"])) is not None]
    default_bortle = statistics.mode(bortles) if bortles else None
    elevation = None
    if args.open_meteo:
        try:
            elevation = app.get_elevation(*center)["elevationM"]
        except Exception as err:  # réseau absent : l'altitude reste à saisir
            report.warn(f"Altitude du lieu non récupérée : {err}")
    location_id = cursor.execute("SELECT id FROM locations WHERE label = 'Jardin'").fetchone()
    if location_id:
        location_id = location_id[0]
    else:
        cursor.execute("INSERT INTO locations (label, lat, lon, elevation_m, bortle, notes) VALUES (?, ?, ?, ?, ?, ?)",
                       ("Jardin", round(center[0], 5), round(center[1], 5), elevation, default_bortle,
                        "Créé par la reprise des données, d'après les coordonnées enregistrées par le Seestar."))
        location_id = cursor.lastrowid

    report.section("Lieu")
    report.line(f"Un seul lieu, **Jardin** : {center[0]:.5f} / {center[1]:.5f} (médiane des coordonnées du Seestar), "
                f"Bortle par défaut {default_bortle} (valeur la plus fréquente des notes)"
                + (f", altitude {elevation:.0f} m." if elevation is not None else "."))
    for key, metres in far:
        report.warn(f"Capture `{key}` à {metres} m du centre : rattachée quand même au Jardin.")

    # --- 3-4. Dates exactes et fusion des fiches d'une même capture
    report.section("Observations reprises")
    report.line("| Capture | Fiches | Avant (début → fin) | Après, d'après les FITS (TU) | Remarques |")
    report.line("|---|---|---|---|---|")
    for key, members in sorted(groups.items(), key=lambda kv: by_key[kv[0]]["start"]):
        capture = by_key[key]
        members.sort(key=lambda o: (0 if (set(map(normalize, o["target_names"])) & name_tokens(capture["names"])) else 1, o["id"]))
        primary, others = members[0], members[1:]
        start, end = f"{capture['start']:%Y-%m-%d %H:%M}", f"{capture['end']:%Y-%m-%d %H:%M}"
        remarks = []
        if any(o["total"] and o["total"] != capture["lights"] for o in members):
            remarks.append(f"total des poses : fiche {primary['total']}, FITS {capture['lights']} (fiche conservée)")
        remarks += [f"{', '.join(o['target_names'])} : {o['reason']}" for o in members if o["reason"]]

        # Notes : identiques → une seule fois ; propres à une fiche → note de sa cible
        session_notes = primary["notes"]
        for other in others:
            if other["notes"].strip() and other["notes"].strip() != session_notes.strip():
                for target_name in other["target_names"]:
                    cursor.execute("""
                        UPDATE observation_targets SET notes = ?
                        WHERE observation_id = ? AND target_id = (SELECT id FROM targets WHERE name = ?)
                    """, (other["notes"], other["id"], target_name))
                remarks.append(f"notes de la fiche {', '.join(other['target_names'])} → note de cette cible")
            # Cibles et images passent sur l'observation conservée (une cible déjà présente n'est pas doublée)
            cursor.execute("""
                UPDATE OR IGNORE observation_targets SET observation_id = ? WHERE observation_id = ?
            """, (primary["id"], other["id"]))
            cursor.execute("UPDATE observation_images SET observation_id = ? WHERE observation_id = ?", (primary["id"], other["id"]))
            cursor.execute("DELETE FROM observations WHERE id = ?", (other["id"],))
        merge_duplicate_images(cursor, primary["id"])

        bortle = next((b for o in members if (b := bortle_from_notes(o["notes"])) is not None), None)
        session_id = app.find_or_create_session(cursor, app.night_of(start), location_id, bortle)
        cursor.execute("UPDATE observations SET start_utc = ?, end_utc = ?, session_id = ?, legacy_location = '' WHERE id = ?",
                       (start, end, session_id, primary["id"]))
        before = ", ".join(sorted({f"{o['start']} → {o['end'][11:] or '?'}" for o in members}))
        report.line(f"| `{key}` | {' + '.join(n for o in members for n in o['target_names'])} | {before} | "
                    f"{start} → {end[11:]} | {'; '.join(remarks)} |")

    # Observations sans capture : gardées telles quelles, rattachées au lieu
    if unmatched:
        report.section("Observations sans capture FITS")
        for obs in unmatched:
            session_id = app.find_or_create_session(cursor, app.night_of(obs["start"]), location_id, bortle_from_notes(obs["notes"]))
            cursor.execute("UPDATE observations SET session_id = ?, legacy_location = '' WHERE id = ?", (session_id, obs["id"]))
            report.warn(f"Fiche {obs['id']} ({', '.join(obs['target_names'])}, {obs['start']}) : aucune capture trouvée, "
                        "date et heures inchangées.")
    app.delete_empty_sessions(cursor)

    orphans = [c for c in captures if c["key"] not in groups]
    if orphans:
        report.section("Captures FITS sans fiche")
        report.line("Ces captures n'ont pas de rapport d'observation ; elles ne sont pas reprises :")
        for c in orphans:
            report.line(f"- `{c['key']}` : {c['start']:%Y-%m-%d %H:%M} → {c['end']:%H:%M} TU, {c['lights']} poses")

    # --- 6. Relevés meteoblue des notes
    report.section("Météo reprise des notes (meteoblue)")
    sessions = cursor.execute("""
        SELECT s.id, s.night_date, group_concat(o.notes, char(10)) FROM sessions s
        JOIN observations o ON o.session_id = s.id GROUP BY s.id ORDER BY s.night_date
    """).fetchall()
    total_readings = 0
    for session_id, night_date, notes in sessions:
        readings = app.parse_meteoblue(notes or "", night_date)
        for r in readings:
            cursor.execute(f"""
                INSERT OR REPLACE INTO weather_readings (session_id, time_utc, {', '.join(app.WEATHER_COLUMNS)}, source, edited)
                VALUES (?, ?, {', '.join('?' * len(app.WEATHER_COLUMNS))}, 'meteoblue', 1)
            """, (session_id, r.time, *(getattr(r, f) for f in app.WEATHER_FIELDS)))
        total_readings += len(readings)
    report.line(f"{total_readings} relevés meteoblue repris, sur {sum(1 for s in sessions if app.parse_meteoblue(s[2] or '', s[1]))} nuits. "
                "Ils sont marqués « meteoblue » et protégés du rafraîchissement.")
    for session_id, night_date, notes in sessions:
        if (notes or "").count("/") >= 5 and "TU" in (notes or "") and not app.parse_meteoblue(notes, night_date):
            report.warn(f"Nuit du {night_date} : les notes semblent contenir de la météo, mais aucune ligne n'a été reconnue.")

    # Météo écrite sans heure (« Clouds 0_0_0 / Arc sec 1.15 / … ») : non reprise, mais comparée aux autres nuits
    labelled = re.compile(r"clouds\s*(\d+)[_-](\d+)[_-](\d+)\s*/\s*arc\s*sec\s*([\d.,]+)\s*/\s*index\s*(\d+)[_-](\d+)"
                          r"\s*/\s*jet\s*stream\s*(\d+)\s*ms\s*/\s*temp\.?\s*(-?\d+)", re.IGNORECASE)
    for session_id, night_date, notes in sessions:
        for m in labelled.finditer(notes or ""):
            values = tuple(float(v.replace(",", ".")) for v in m.groups())
            twin = cursor.execute("""
                SELECT s.night_date, w.time_utc FROM weather_readings w JOIN sessions s ON s.id = w.session_id
                WHERE s.id != ? AND w.cloud_low = ? AND w.cloud_mid = ? AND w.cloud_high = ? AND w.seeing_arcsec = ?
                  AND w.index1 = ? AND w.index2 = ? AND w.jet_stream_ms = ? AND w.temp_c = ?
            """, (session_id, *values)).fetchone()
            report.warn(f"Nuit du {night_date} : météo notée sans heure (« {m.group(0)[:60]}… »), non reprise"
                        + (f" ; valeurs identiques au relevé du {twin[1]} (nuit du {twin[0]}) : copie probable." if twin else "."))

    # Copie suspecte : même relevé sur deux nuits différentes
    seen = {}
    for session_id, night_date, *values in cursor.execute(f"""
            SELECT w.session_id, s.night_date, {', '.join('w.' + c for c in app.WEATHER_COLUMNS)}
            FROM weather_readings w JOIN sessions s ON s.id = w.session_id"""):
        key = tuple(values)
        if key in seen and seen[key] != night_date:
            report.warn(f"Relevé meteoblue identique les nuits du {seen[key]} et du {night_date} : copie possible.")
        seen.setdefault(key, night_date)

    conn.commit()

    # --- 7. Open-Meteo pour les heures sans relevé
    if args.open_meteo:
        fetched = failed = 0
        for (session_id,) in cursor.execute("SELECT id FROM sessions").fetchall():
            try:
                app.fetch_weather(session_id)
                fetched += 1
            except Exception as err:
                failed += 1
                report.warn(f"Session {session_id} : Open-Meteo indisponible ({getattr(err, 'detail', err)}).")
        report.line(f"\nOpen-Meteo : {fetched} nuits complétées" + (f", {failed} en échec." if failed else "."))

    # --- Contrôles
    report.section("Contrôles")
    problems = conn.execute("PRAGMA foreign_key_check").fetchall()
    report.line(f"Intégrité des références : {'OK' if not problems else problems}  ")
    counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
              for t in ("observations", "observation_targets", "observation_images", "sessions", "weather_readings")}
    report.line("  \n".join(f"{t} : {n}" for t, n in counts.items()))

    app.write_setting(cursor, MIGRATION_KEY, datetime.now().strftime("%Y-%m-%d %H:%M"))
    conn.commit()
    conn.close()

    report_path = args.out / "compte-rendu-reprise.md"
    report.save(report_path)
    print(f"Base reprise : {db_path}\nCompte rendu : {report_path}")


def merge_duplicate_images(cursor, observation_id: int):
    """Deux fiches conjointes partageaient souvent le même fichier : une seule image, avec toutes les cibles."""
    rows = cursor.execute("SELECT id, path, is_favorite FROM observation_images WHERE observation_id = ? ORDER BY position, id",
                          (observation_id,)).fetchall()
    kept = {}
    for image_id, path, favorite in rows:
        key = path.lower()
        if key not in kept:
            kept[key] = image_id
            continue
        cursor.execute("UPDATE OR IGNORE image_targets SET image_id = ? WHERE image_id = ?", (kept[key], image_id))
        cursor.execute("DELETE FROM observation_images WHERE id = ?", (image_id,))
    # Une seule favorite : la première
    favorites = [i for (i,) in cursor.execute(
        "SELECT id FROM observation_images WHERE observation_id = ? AND is_favorite = 1 ORDER BY position, id", (observation_id,))]
    for image_id in favorites[1:]:
        cursor.execute("UPDATE observation_images SET is_favorite = 0 WHERE id = ?", (image_id,))
    for position, (image_id,) in enumerate(cursor.execute(
            "SELECT id FROM observation_images WHERE observation_id = ? ORDER BY is_favorite DESC, position, id", (observation_id,)).fetchall()):
        cursor.execute("UPDATE observation_images SET position = ? WHERE id = ?", (position, image_id))


class Report:
    def __init__(self):
        self.parts = ["# Reprise des observations : compte rendu\n"]
        self.warnings = []

    def section(self, title):
        self.parts.append(f"\n## {title}\n")

    def line(self, text):
        self.parts.append(text)

    def warn(self, text):
        self.warnings.append(text)
        self.parts.append(f"- ⚠ {text}")

    def save(self, path: Path):
        summary = ["\n## À vérifier\n"] + ([f"- {w}" for w in self.warnings] or ["Rien à signaler."])
        path.write_text("\n".join(self.parts[:1] + summary + self.parts[1:]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
