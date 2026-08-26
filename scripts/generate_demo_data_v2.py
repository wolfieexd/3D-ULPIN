import os
import json
import csv
import math
import random

OUT_DIR = os.path.join("frontend", "public", "data")
os.makedirs(OUT_DIR, exist_ok=True)
CSV_PATH = r"../data/raw/open_buildings_v3_chennai.csv"
TARGET_LON = 80.205000
TARGET_LAT = 13.085000
RADIUS = 0.005 

def parse_wkt_polygon(wkt_str):
    try:
        content = wkt_str.replace('POLYGON((', '').replace('POLYGON ((', '').replace('))', '')
        points_str = content.split(',')
        coords = []
        for p in points_str:
            lon, lat = p.strip().split(' ')
            coords.append([float(lon), float(lat)])
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        return [coords]
    except Exception as e:
        return None

def buffer_polygon(coords, scale=1.2):
    buffered = []
    center_lon = sum(p[0] for p in coords[0]) / len(coords[0])
    center_lat = sum(p[1] for p in coords[0]) / len(coords[0])
    for lon, lat in coords[0]:
        dlon = lon - center_lon
        dlat = lat - center_lat
        buffered.append([center_lon + dlon * scale, center_lat + dlat * scale])
    buffered[-1] = buffered[0]
    return [buffered]

real_buildings = []
try:
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            lon = float(row['longitude'])
            lat = float(row['latitude'])
            dist = math.sqrt((lon - TARGET_LON)**2 + (lat - TARGET_LAT)**2)
            if dist < RADIUS:
                geom = parse_wkt_polygon(row['geometry'])
                if geom:
                    real_buildings.append({
                        "id": row['full_plus_code'],
                        "lon": lon,
                        "lat": lat,
                        "area": float(row['area_in_meters']),
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": geom
                        }
                    })
except Exception as e:
    print("Error parsing CSV:", e)

real_buildings.sort(key=lambda x: x['area'], reverse=True)
demo_buildings_raw = real_buildings[:300]
print(f"Loaded {len(demo_buildings_raw)} buildings.")

parcels = []
buildings = []
floors = []
units = []
utilities = []
conflicts = []

for i, bld in enumerate(demo_buildings_raw):
    is_primary = (i == 0)
    parcel_id = "P000001" if is_primary else f"P{i+1:06d}"
    building_id = "B001" if is_primary else f"B{i+1:03d}"
    ulpin = "DEMO-TN-CHN-000001" if is_primary else f"DEMO-TN-CHN-{i+1:06d}"
    
    if i < 10:
        parcels.append({
            "type": "Feature",
            "properties": {
                "parcel_id": parcel_id,
                "demo_ulpin": ulpin,
                "survey_number": f"104/{i+1}A",
                "area_sqm": bld['area'] * 1.5,
                "is_primary": is_primary,
                "data_status": "DEMO / SYNTHETIC",
                "source": "Synthetic Cadastre"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": buffer_polygon(bld['geometry']['coordinates'])
            }
        })
    
    buildings.append({
        "type": "Feature",
        "properties": {
            "building_id": building_id,
            "parcel_id": parcel_id,
            "demo_ulpin": ulpin,
            "height": 12.8 if is_primary else random.choice([3.2, 6.4, 9.6, 12.8]),
            "floors": 4 if is_primary else random.choice([1, 2, 3]),
            "is_primary": is_primary,
            "data_status": "REAL FOOTPRINT / SYNTHETIC HEIGHT",
            "source": "Google Open Buildings"
        },
        "geometry": bld['geometry']
    })

FLOOR_HEIGHT = 3.2
hero_bld = buildings[0]
h_parcel_id = hero_bld["properties"]["parcel_id"]
h_building_id = hero_bld["properties"]["building_id"]
h_ulpin = hero_bld["properties"]["demo_ulpin"]

coords = hero_bld["geometry"]["coordinates"][0]
min_lon = min(p[0] for p in coords)
max_lon = max(p[0] for p in coords)
min_lat = min(p[1] for p in coords)
max_lat = max(p[1] for p in coords)
mid_lon = (min_lon + max_lon) / 2
mid_lat = (min_lat + max_lat) / 2

inset = 0.000015
quads = [
    [[min_lon+inset, min_lat+inset], [mid_lon-inset, min_lat+inset], [mid_lon-inset, mid_lat-inset], [min_lon+inset, mid_lat-inset], [min_lon+inset, min_lat+inset]],
    [[mid_lon+inset, min_lat+inset], [max_lon-inset, min_lat+inset], [max_lon-inset, mid_lat-inset], [mid_lon+inset, mid_lat-inset], [mid_lon+inset, min_lat+inset]],
    [[min_lon+inset, mid_lat+inset], [mid_lon-inset, mid_lat+inset], [mid_lon-inset, max_lat-inset], [min_lon+inset, max_lat-inset], [min_lon+inset, mid_lat+inset]],
    [[mid_lon+inset, mid_lat+inset], [max_lon-inset, mid_lat+inset], [max_lon-inset, max_lat-inset], [mid_lon+inset, max_lat-inset], [mid_lon+inset, mid_lat+inset]]
]

for f in range(4):
    floor_id = f"{h_building_id}-F{f+1:02d}"
    z_min = f * FLOOR_HEIGHT
    z_max = (f + 1) * FLOOR_HEIGHT
    
    floors.append({
        "type": "Feature",
        "properties": {
            "floor_id": floor_id,
            "building_id": h_building_id,
            "parcel_id": h_parcel_id,
            "floor_number": f + 1,
            "z_min": z_min,
            "z_max": z_max,
            "data_status": "DEMO / SYNTHETIC"
        },
        "geometry": hero_bld["geometry"]
    })
    
    for u in range(4):
        unit_id = f"{floor_id}-U{u+1:02d}"
        prop_id = f"3D-CHN-{h_parcel_id}-{unit_id}"
        
        unit_feat = {
            "type": "Feature",
            "properties": {
                "unit_id": unit_id,
                "floor_id": floor_id,
                "building_id": h_building_id,
                "parcel_id": h_parcel_id,
                "demo_ulpin": h_ulpin,
                "property_3d_id": prop_id,
                "area_sqm": 75.0,
                "z_min": z_min,
                "z_max": z_max,
                "height": z_max - z_min,
                "volume_m3": 75.0 * (z_max - z_min),
                "data_status": "DEMO / SYNTHETIC"
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [quads[u]]
            }
        }
        units.append(unit_feat)

center_lon = demo_buildings_raw[0]['lon']
center_lat = demo_buildings_raw[0]['lat']

utilities.append({
    "type": "Feature",
    "properties": {
        "utility_id": "UTIL-WATER-001",
        "type": "WATER",
        "z_min": -2.5,
        "z_max": -1.5,
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [center_lon - 0.001, center_lat],
            [center_lon + 0.001, center_lat]
        ]
    }
})
utilities.append({
    "type": "Feature",
    "properties": {
        "utility_id": "UTIL-SEWER-001",
        "type": "SEWER",
        "z_min": -2.0,
        "z_max": -1.0,
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "LineString",
        "coordinates": [
            [center_lon, center_lat - 0.001],
            [center_lon, center_lat + 0.001]
        ]
    }
})

conflicts.append({
    "type": "Feature",
    "properties": {
        "conflict_id": "CONF-001",
        "type": "3D Spatial Overlap",
        "feature_a": "UTIL-WATER-001",
        "feature_b": "UTIL-SEWER-001",
        "overlap_m": 0.5,
        "description": "Vertical Utility Collision"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [center_lon, center_lat]
    }
})

def validate_data():
    b_ids = [b['properties']['building_id'] for b in buildings]
    f_ids = [f['properties']['floor_id'] for f in floors]
    u_ids = [u['properties']['unit_id'] for u in units]
    p3d_ids = [u['properties']['property_3d_id'] for u in units]
    
    assert len(b_ids) == len(set(b_ids)), "Duplicate Building IDs found"
    assert len(f_ids) == len(set(f_ids)), "Duplicate Floor IDs found"
    assert len(u_ids) == len(set(u_ids)), "Duplicate Unit IDs found"
    assert len(p3d_ids) == len(set(p3d_ids)), "Duplicate 3D Property IDs found"
    
    for u in units:
        assert u['properties']['z_min'] >= 0, "Unit Z below 0"
        
validate_data()

def write_geojson(filename, features):
    with open(os.path.join(OUT_DIR, filename), 'w') as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)

write_geojson("parcels.geojson", parcels)
write_geojson("buildings.geojson", buildings)
write_geojson("floors.geojson", floors)
write_geojson("units.geojson", units)
write_geojson("utilities.geojson", utilities)
write_geojson("conflicts.geojson", conflicts)

print("Data generated successfully with strict cadastral hierarchy.")
