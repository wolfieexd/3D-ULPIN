import json
import os

OUT_DIR = os.path.join("frontend", "public", "data")

def shift_geojson(filename, lon_shift, lat_shift):
    path = os.path.join(OUT_DIR, filename)
    if not os.path.exists(path): return
    with open(path, 'r') as f:
        data = json.load(f)
    
    def shift_coords(coords):
        if isinstance(coords[0], (int, float)):
            return [coords[0] + lon_shift, coords[1] + lat_shift]
        return [shift_coords(c) for c in coords]
        
    for feature in data.get('features', []):
        geom = feature.get('geometry')
        if geom:
            geom['coordinates'] = shift_coords(geom['coordinates'])
            
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    repo_path = os.path.join("data/demo", filename)
    with open(repo_path, 'w') as f:
        json.dump(data, f, indent=2)

# Apply a visual shift of -0.00008 lon (West), -0.0001 lat (South)
shift_geojson("parcels.geojson", -0.00008, -0.00010)
shift_geojson("buildings.geojson", -0.00008, -0.00010)
shift_geojson("floors.geojson", -0.00008, -0.00010)
shift_geojson("units.geojson", -0.00008, -0.00010)
shift_geojson("utilities.geojson", -0.00008, -0.00010)
shift_geojson("conflicts.geojson", -0.00008, -0.00010)

print("Shifted all geojson files to align with OSM.")
