import os
import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Configuration CORS pour autoriser l'interface Tauri (localhost:1420 ou tauri://localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "allnightlong.db"

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

class ObservationSchema(BaseModel):
    id: Optional[int] = None
    targetId: int
    date: str
    obsStart: str = ""
    obsEnd: str = ""
    location: str = ""
    altitude: str = ""
    sensor: str = ""
    filter: str = ""
    sensorTemp: str = ""
    subExposure: str = ""
    imgTotal: int = 0
    imgGood: int = 0
    imgPass: int = 0
    imgBad: int = 0
    otherObjects: str = ""
    imageRaw: str = ""
    imageProcessed: str = ""


# ================= INITIALISATION DE LA BASE SQLITE =================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Table des Objets (Targets)
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
        
    conn.commit()
    conn.close()

# Initialisation au démarrage
init_db()

# ================= ENDPOINTS API (FastAPI) =================

@app.get("/api/targets", response_model=List[TargetSchema])
def get_targets():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref FROM targets")
    rows = cursor.fetchall()
    conn.close()
    
    # On reconstruit les objets JSON pour matcher notre frontend
    return [
        TargetSchema(
            id=r[0], name=r[1], usualName=r[2], constellation=r[3], otherDesignations=r[4],
            type=r[5], group=r[6], magnitude=r[7], colorIndex=r[8], surfBrightness=r[9],
            size=r[10], ra=r[11], dec=r[12], imageRef=r[13]
        ) for r in rows
    ]

@app.post("/api/targets", response_model=TargetSchema)
def save_target(target: TargetSchema):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if target.id:
        # Mise à jour
        cursor.execute("""
            UPDATE targets SET name=?, usual_name=?, constellation=?, other_designations=?, type=?, group_name=?, magnitude=?, color_index=?, surf_brightness=?, size=?, ra=?, dec=?, image_ref=?
            WHERE id=?
        """, (target.name, target.usualName, target.constellation, target.otherDesignations, target.type, target.group, target.magnitude, target.colorIndex, target.surfBrightness, target.size, target.ra, target.dec, target.imageRef, target.id))
        target_id = target.id
    else:
        # Création
        cursor.execute("""
            INSERT INTO targets (name, usual_name, constellation, other_designations, type, group_name, magnitude, color_index, surf_brightness, size, ra, dec, image_ref)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (target.name, target.usualName, target.constellation, target.otherDesignations, target.type, target.group, target.magnitude, target.colorIndex, target.surfBrightness, target.size, target.ra, target.dec, target.imageRef))
        target_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    target.id = target_id
    return target

@app.delete("/api/targets/{target_id}")
def delete_target(target_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DELETE FROM targets WHERE id=?", (target_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/api/targets/{target_id}/observations", response_model=List[ObservationSchema])
def get_observations(target_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, target_id, date, obs_start, obs_end, location, altitude, sensor, filter, sensor_temp, sub_exposure, img_total, img_good, img_pass, img_bad, other_objects, image_raw, image_processed
        FROM observations WHERE target_id=?
    """, (target_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        ObservationSchema(
            id=r[0], targetId=r[1], date=r[2], obsStart=r[3], obsEnd=r[4], location=r[5],
            altitude=r[6], sensor=r[7], filter=r[8], sensorTemp=r[9], subExposure=r[10],
            imgTotal=r[11], imgGood=r[12], imgPass=r[13], imgBad=r[14], otherObjects=r[15],
            imageRaw=r[16], imageProcessed=r[17]
        ) for r in rows
    ]

@app.post("/api/observations", response_model=ObservationSchema)
def save_observation(obs: ObservationSchema):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if obs.id and obs.id > 1000000000: # Détecte un ID temporaire JS (timestamp) pour forcer la création
        obs.id = None
        
    if obs.id:
        # Mise à jour
        cursor.execute("""
            UPDATE observations SET date=?, obs_start=?, obs_end=?, location=?, altitude=?, sensor=?, filter=?, sensor_temp=?, sub_exposure=?, img_total=?, img_good=?, img_pass=?, img_bad=?, other_objects=?, image_raw=?, image_processed=?
            WHERE id=?
        """, (obs.date, obs.obsStart, obs.obsEnd, obs.location, obs.altitude, obs.sensor, obs.filter, obs.sensorTemp, obs.subExposure, obs.imgTotal, obs.imgGood, obs.imgPass, obs.imgBad, obs.otherObjects, obs.imageRaw, obs.imageProcessed, obs.id))
        obs_id = obs.id
    else:
        # Création
        cursor.execute("""
            INSERT INTO observations (target_id, date, obs_start, obs_end, location, altitude, sensor, filter, sensor_temp, sub_exposure, img_total, img_good, img_pass, img_bad, other_objects, image_raw, image_processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (obs.targetId, obs.date, obs.obsStart, obs.obsEnd, obs.location, obs.altitude, obs.sensor, obs.filter, obs.sensorTemp, obs.subExposure, obs.imgTotal, obs.imgGood, obs.imgPass, obs.imgBad, obs.otherObjects, obs.imageRaw, obs.imageProcessed))
        obs_id = cursor.lastrowid
        
    conn.commit()
    conn.close()
    obs.id = obs_id
    return obs

@app.delete("/api/observations/{obs_id}")
def delete_observation(obs_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM observations WHERE id=?", (obs_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    # Démarre le serveur web FastAPI sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)