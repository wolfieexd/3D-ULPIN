import os
import json
import csv
import math
import random
from shapely.geometry import Polygon as ShapelyPolygon, box, LineString

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
    pass

real_buildings.sort(key=lambda x: x['area'], reverse=True)
demo_buildings_raw = real_buildings[:300]

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
hero_poly = ShapelyPolygon(coords)
minx, miny, maxx, maxy = hero_poly.bounds
midx = (minx + maxx) / 2
midy = (miny + maxy) / 2

quads = [
    box(minx, miny, midx, midy),
    box(midx, miny, maxx, midy),
    box(minx, midy, midx, maxy),
    box(midx, midy, maxx, maxy)
]

unit_geoms = []
for q in quads:
    intersection = hero_poly.intersection(q)
    if not intersection.is_empty:
        if intersection.geom_type == 'Polygon':
            unit_geoms.append(list(intersection.exterior.coords))
        elif intersection.geom_type == 'MultiPolygon':
            largest = max(intersection.geoms, key=lambda a: a.area)
            unit_geoms.append(list(largest.exterior.coords))

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
    
    for u in range(min(4, len(unit_geoms))):
        unit_id = f"{floor_id}-U{u+1:02d}"
        prop_id = f"3D-CHN-{h_parcel_id}-{unit_id}"
        
        area_m2 = ShapelyPolygon(unit_geoms[u]).area * 1e10
        
        units.append({
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
                "coordinates": [[list(p) for p in unit_geoms[u]]]
            }
        })

# ADD UTILITIES
water_line = [[minx - 0.0001, midy], [maxx + 0.0001, midy]]
sewer_line = [[midx, miny - 0.0001], [midx, maxy + 0.0001]]

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
        "coordinates": water_line
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
        "coordinates": sewer_line
    }
})

conflicts.append({
    "type": "Feature",
    "properties": {
        "conflict_id": "CONF-001",
        "utility_1": "UTIL-WATER-001",
        "utility_2": "UTIL-SEWER-001",
        "z_overlap_min": -2.0,
        "z_overlap_max": -1.5,
        "description": "WATER <-> SEWER SPATIAL OVERLAP",
        "data_status": "DEMO / SYNTHETIC"
    },
    "geometry": {
        "type": "Point",
        "coordinates": [midx, midy]
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
write_geojson("conflicts.geojson", conflicts)

print("Data generated successfully.")
