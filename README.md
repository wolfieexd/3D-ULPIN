# 3D ULPIN — Chennai Vertical Property & Land Intelligence

## Problem Statement
**26011 - Creating a 3D Property Cadastral System using ULPIN**

Current cadastral systems largely map 2D land parcels. However, modern urban development features vertically structured properties (apartments, underground utilities, multi-floor ownership) which demand a **3D Cadastral Framework**. 

This prototype visualizes a real-world subset of Chennai building footprints mapped to a synthetic cadastral and vertical-ownership data model (ULPIN).

## Architecture
- **Frontend**: React + Vite + Tailwind CSS
- **3D Engine**: Cesium (Resium wrappers)
- **Backend**: FastAPI (Python) serving GeoJSON features
- **Data Generation**: Python (GeoPandas + Shapely) for intersection & cadastral structuring

## Real vs Synthetic Data
- **REAL / OPEN DATA**: The contextual building footprints (300 surrounding footprints and the base hero footprint) are derived from the **Google Open Buildings** dataset (CC BY-4.0).
- **DEMO / SYNTHETIC DATA**: The cadastral parcel, Demo ULPIN (`DEMO-TN-CHN-000001`), ownership records, floor counts, z-axis extrusion, subdivided units (`B001-F03-U02`), and underground utilities are strictly synthetic demonstration data. They do *not* represent official government records.

## Project Structure
```
3D-ULPIN/
├── frontend/          # React + Cesium 3D Viewer
├── backend/           # FastAPI backend serving GeoJSON
├── scripts/           # Data generation/intersection logic
└── data/
    └── demo/          # The generated subset used by the application
```

## Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (3.10+)

### 1. Start the Backend API
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app/main.py
```
The API will start at `http://localhost:8000/`.

### 2. Start the Frontend Application
Open a new terminal window:
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## SIH Demo Mode
The application includes a fully automated cinematic walkthrough. 
Simply click **"START SIH DEMO"** in the top-right corner to step through the 15 phases of 3D Cadastral mapping, ending with a live spatial conflict detection.

## Generating Demo Data (Optional)
The repository includes pre-generated data inside `data/demo/` for zero-setup execution. If you wish to examine the geometric intersection logic:
```powershell
cd scripts
python generate_demo_data_v4.py
```

## Data Sources
- **Building Footprints**: Google Open Buildings (https://sites.research.google/open-buildings/)
- **Basemap**: OpenStreetMap contributors

## License
MIT License. 
