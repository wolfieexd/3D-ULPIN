content = """<div align="center">
  <h1>🏙️ 3D ULPIN</h1>
  <p><strong>Chennai Vertical Property & Land Intelligence System</strong></p>
  
  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Cesium](https://img.shields.io/badge/CesiumJS-63A532?style=for-the-badge&logo=cesium&logoColor=white)](https://cesium.com/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
</div>

<br />

## 📖 Problem Statement (SIH 2026 - 26011)
**Creating a 3D Property Cadastral System using ULPIN**

Current cadastral systems largely map land parcels in 2D. However, modern urban development features highly complex, vertically structured properties—such as multi-story apartments, subterranean infrastructure, and layered ownership. These demand a **True 3D Cadastral Framework**. 

This repository serves as a prototype visualization for the **Smart India Hackathon**. It projects a real-world subset of Chennai building footprints onto a synthetic 3D cadastral and vertical-ownership data model linked by a Unique Land Parcel Identification Number (ULPIN).

---

## ✨ Key Features
- 🌍 **High-Performance 3D WebGIS**: Powered by CesiumJS to render complex spatial data in the browser with zero plugins.
- 🏢 **Vertical Property Subdivision**: Hierarchical structuring mapping `Parcel ➔ Building ➔ Floor ➔ Unit`.
- 🔍 **Interactive Property Inspector**: Click any real-world building to extrude and dissect its 3D units, fetching exact Z-axis bounds and volumetric data.
- 🚇 **Subterranean Spatial Conflict Detection**: Visualizes underground utility overlaps (e.g., Water vs. Sewer intersections) beneath specific properties.
- 🎬 **Automated SIH Demo Mode**: A cinematic, 15-step automated camera walkthrough designed specifically for presentation pitches.

---

## 🏗️ System Architecture
The platform is built on a decoupled modern web stack:

- **Frontend (UI & 3D Visualization)**: React 18, Vite, Tailwind CSS, and Resium (React wrappers for CesiumJS).
- **Backend (Spatial API)**: FastAPI (Python) running on Uvicorn, serving pre-processed GeoJSON layers.
- **Data Pipeline**: Python scripts utilizing `GeoPandas` and `Shapely` for complex geometric intersections, bounding-box calculations, and synthetic cadastral assignments.

---

## 📊 Data Provenance: Real vs. Synthetic
To demonstrate the system without exposing sensitive government records, the data is split into two distinct tiers:

> [!IMPORTANT]
> **REAL / OPEN DATA**  
> The contextual building footprints (the 300 surrounding footprints and the base hero footprint) are derived from the [Google Open Buildings](https://sites.research.google/open-buildings/) dataset (CC BY-4.0). The basemap imagery is provided by OpenStreetMap.

> [!NOTE]  
> **DEMO / SYNTHETIC DATA**  
> The cadastral parcel mapping, Demo ULPIN (`DEMO-TN-CHN-000001`), ownership records, floor counts, Z-axis extrusions, subdivided units (`B001-F03-U02`), and underground utility lines are strictly synthetic demonstration data generated via Python for the Hackathon.

---

## 🚀 Quick Start Guide

### Prerequisites
- [Node.js](https://nodejs.org/) (v18 or higher)
- [Python](https://www.python.org/) (3.10 or higher)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/wolfieexd/3D-ULPIN.git
cd 3D-ULPIN
```

### 2. Launch the FastAPI Backend
The backend is required to serve the GeoJSON spatial data to the frontend.
```powershell
cd backend
python -m venv venv
.\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python app/main.py
```
> The API will start at `http://localhost:8000/`. You can verify it is running by navigating to `http://localhost:8000/api/health`.

### 3. Launch the React 3D Frontend
Open a **new terminal window** and navigate to the frontend directory:
```powershell
cd frontend
npm install
npm run dev
```
> Open `http://localhost:5173` in your web browser to view the application.

---

## 🎥 Automated SIH Presentation Mode
The application includes a fully automated cinematic walkthrough tailored for the hackathon judging criteria. 
1. Open the application in your browser.
2. Click the blue **"START SIH DEMO"** button in the top-right corner.
3. The camera will automatically guide you through all 15 phases of 3D Cadastral mapping—beginning at the macro Chennai neighborhood scale, isolating the hero building, subdividing the 3D property, and concluding with a live underground spatial conflict detection.

---

## 🛠️ Data Engineering (Optional)
The repository includes the pre-generated static data inside `data/demo/` for instant, zero-setup execution. However, if you wish to inspect or modify the geometric intersection logic that generated the demo units:

```powershell
cd scripts
python generate_demo_data_v4.py
```
*Note: You must acquire the raw Google Open Buildings CSV and place it in the designated `/data/raw` folder to run the generation pipeline from scratch.*

---

## 📜 License & Attribution
- **Source Code**: MIT License 
- **Building Footprints**: Google Open Buildings (CC BY-4.0)
- **Basemap Imagery**: © OpenStreetMap contributors
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)
