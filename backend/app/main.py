from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import json
import os

app = FastAPI(title="3D ULPIN Demo API")

# Allow CORS for local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "../../data/demo")

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {"type": "FeatureCollection", "features": []}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "3D ULPIN System Online"}

@app.get("/api/demo")
def get_demo_metadata():
    return load_json("demo_metadata.json")

@app.get("/api/parcels")
def get_parcels():
    return load_json("parcels.geojson")

@app.get("/api/buildings")
def get_buildings():
    return load_json("buildings.geojson")

@app.get("/api/properties")
def get_properties():
    return load_json("property_volumes.geojson")

@app.get("/api/floors")
def get_floors():
    return load_json("floors.geojson")

@app.get("/api/units")
def get_units():
    return load_json("units.geojson")

@app.get("/api/utilities")
def get_utilities():
    return load_json("utilities.geojson")

@app.get("/api/conflicts")
def get_conflicts():
    return load_json("conflicts.geojson")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
