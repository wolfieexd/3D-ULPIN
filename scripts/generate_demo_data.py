import json
import random
import os

random.seed(42)

OUT_DIR = "../data/demo"
os.makedirs(OUT_DIR, exist_ok=True)

# Base coordinates for Chennai demonstration area
CENTER_LON = 80.205000
CENTER_LAT = 13.085000

def offset(lon, lat, dx, dy):
    # Rough approximation: 1 degree approx 111km
    return [lon + dx / 111000.0, lat + dy / 111000.0]

def create_polygon(center_lon, center_lat, w, h):
    return [
        offset(center_lon, center_lat, -w/2, -h/2),
        offset(center_lon, center_lat, w/2, -h/2),
        offset(center_lon, center_lat, w/2, h/2),
        offset(center_lon, center_lat, -w/2, h/2),
        offset(center_lon, center_lat, -w/2, -h/2)
    ]

# 1. PARCELS
parcels = []
# Primary Demo Parcel
parcels.append({
    "type": "Feature",
    "properties": {
        "parcel_id": "P000001",
        "demo_ulpin": "DEMO-TN-CHN-000001",
        "survey_number": "104/2A",
        "area_sqm": 1200.0,
        "is_primary": True,
        "data_status": "DEMO / SYNTHETIC",
        "source": "Synthetic Cadastre"
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [create_polygon(CENTER_LON, CENTER_LAT, 40, 30)]
    }
})

# Generate a few more context parcels
for i in range(2, 6):
    d_lon = random.uniform(-60, 60)
    d_lat = random.uniform(-60, 60)
    parcels.append({
        "type": "Feature",
        "properties": {
            "parcel_id": f"P{i:06d}",
            "demo_ulpin": f"DEMO-TN-CHN-{i:06d}",
            "survey_number": f"104/{i}B",
            "area_sqm": random.uniform(800, 1500),
            "is_primary": False,
            "data_status": "DEMO / SYNTHETIC",
            "source": "Synthetic Cadastre"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [create_polygon(CENTER_LON + d_lon/111000, CENTER_LAT + d_lat/111000, random.uniform(20, 40), random.uniform(20, 30))]
        }
    })

# 2. BUILDINGS
buildings = []
# Primary Building
buildings.append({
    "type": "Feature",
    "properties": {
        "building_id": "B01",
        "parcel_id": "P000001",
        "height": 12.8,
        "floors": 4,
        "is_primary": True,
        "data_status": "DEMO / SYNTHETIC",
        "source": "Synthetic Demonstration Dataset"
    },
    "geometry": {
        "type": "Polygon",
        "coordinates": [create_polygon(CENTER_LON, CENTER_LAT, 25, 15)]
    }
})

# Context buildings
for i, p in enumerate(parcels[1:]):
    buildings.append({
        "type": "Feature",
        "properties": {
            "building_id": f"B{i+2:02d}",
            "parcel_id": p["properties"]["parcel_id"],
            "height": random.choice([3.2, 6.4, 9.6]),
            "floors": random.choice([1, 2, 3]),
            "is_primary": False,
            "data_status": "DEMO / SYNTHETIC",
            "source": "Synthetic Demonstration Dataset"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": p["geometry"]["coordinates"] # simplify: use slightly smaller footprint later if needed, for now just reuse or shrink
        }
    })
    # Shrink context building
    poly = buildings[-1]["geometry"]["coordinates"][0]
    buildings[-1]["geometry"]["coordinates"] = [[
        [(c[0]+CENTER_LON)/2, (c[1]+CENTER_LAT)/2] for c in poly # naive shrink
    ]]

# 3. FLOORS & UNITS FOR PRIMARY BUILDING
floors = []
units = []
property_volumes = []
FLOOR_HEIGHT = 3.2

primary_poly = buildings[0]["geometry"]["coordinates"][0]

for f in range(4):
    floor_id = f"F{f+1:02d}"
    z_min = f * FLOOR_HEIGHT
    z_max = (f + 1) * FLOOR_HEIGHT
    
    floors.append({
        "type": "Feature",
        "properties": {
            "floor_id": floor_id,
            "building_id": "B01",
            "level": f + 1,
            "z_min": z_min,
            "z_max": z_max,
            "data_status": "DEMO / SYNTHETIC"
        },
        "geometry": buildings[0]["geometry"]
    })
    
    # Split floor into 4 units (quadrants)
    w = 25
    h = 15
    quads = [
        # bottom-left
        create_polygon(CENTER_LON - w/4/111000, CENTER_LAT - h/4/111000, w/2, h/2),
        # bottom-right
        create_polygon(CENTER_LON + w/4/111000, CENTER_LAT - h/4/111000, w/2, h/2),
        # top-left
        create_polygon(CENTER_LON - w/4/111000, CENTER_LAT + h/4/111000, w/2, h/2),
        # top-right
        create_polygon(CENTER_LON + w/4/111000, CENTER_LAT + h/4/111000, w/2, h/2),
    ]
    
    for u in range(4):
        unit_id = f"U{u+1:02d}"
        prop_id = f"3D-CHN-P000001-B01-{floor_id}-{unit_id}"
        
        unit_feat = {
            "type": "Feature",
            "properties": {
                "unit_id": unit_id,
                "floor_id": floor_id,
                "property_3d_id": prop_id,
                "area_sqm": (w/2)*(h/2),
                "z_min": z_min,
                "z_max": z_max,
                "volume_m3": ((w/2)*(h/2)) * FLOOR_HEIGHT,
                "data_status": "DEMO / SYNTHETIC"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [quads[u]]
            }
        }
        units.append(unit_feat)
        property_volumes.append(unit_feat)

# 4. UNDERGROUND UTILITIES
utilities = []
utilities.append({
    "type": "Feature",
    "properties": {
        "utility_id": "UTIL-WATER-001",
        "type": "WATER",
        "z_min": -2.0,
        "z_max": -1.5,
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            offset(CENTER_LON, CENTER_LAT, -50, 0),
            offset(CENTER_LON, CENTER_LAT, 50, 0)
        ]
    }
})
utilities.append({
    "type": "Feature",
    "properties": {
        "utility_id": "UTIL-SEWER-001",
        "type": "SEWER",
        "z_min": -3.5,
        "z_max": -2.5,
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            offset(CENTER_LON, CENTER_LAT, -50, -5),
            offset(CENTER_LON, CENTER_LAT, 50, -5)
        ]
    }
})
utilities.append({
    "type": "Feature",
    "properties": {
        "utility_id": "UTIL-ELEC-001",
        "type": "ELECTRICAL",
        "z_min": -1.5,
        "z_max": -1.0,
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            offset(CENTER_LON, CENTER_LAT, -50, 5),
            offset(CENTER_LON, CENTER_LAT, 50, 5)
        ]
    }
})

# CONFLICT
conflicts = []
conflicts.append({
    "type": "Feature",
    "properties": {
        "conflict_id": "CONF-001",
        "type": "3D Spatial Overlap",
        "property_id": "3D-CHN-P000001-B01-BASEMENT",
        "infrastructure_id": "UTIL-WATER-001",
        "overlap_m": 0.5,
        "severity": "HIGH",
        "description": "Property basement volume (Z: -1.5 to 0.0) conflicts with Water Line (Z: -2.0 to -1.5)"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [CENTER_LON, CENTER_LAT]
    }
})

def write_geojson(filename, features):
    with open(os.path.join(OUT_DIR, filename), 'w') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

write_geojson("parcels.geojson", parcels)
write_geojson("buildings.geojson", buildings)
write_geojson("floors.geojson", floors)
write_geojson("units.geojson", units)
write_geojson("utilities.geojson", utilities)
write_geojson("property_volumes.geojson", property_volumes)
write_geojson("conflicts.geojson", conflicts)

# Metadata
with open(os.path.join(OUT_DIR, "demo_metadata.json"), 'w') as f:
    json.dump({
        "project": "3D ULPIN",
        "location": "Chennai, TN",
        "center": [CENTER_LON, CENTER_LAT],
        "primary_ulpin": "DEMO-TN-CHN-000001",
        "crs": "EPSG:4326"
    }, f, indent=2)

print("Demo data generated successfully.")
