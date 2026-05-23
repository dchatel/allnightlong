# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuration CORS pour autoriser Tauri (localhost:1420 ou tauri://localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En développement, en prod restreindre à "tauri://localhost"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Serveur AstroLab prêt !"}

@app.get("/observations")
def get_observations():
    # Ici tu feras tes requêtes SQLite plus tard
    return [{"id": 1, "target": "M42", "type": "Nebula"}]

if __name__ == "__main__":
    import uvicorn
    # Démarre le serveur sur le port 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)