import json

with open('frontend/public/data/buildings.geojson', 'r') as f:
    data = json.load(f)

print("=== SPATIAL DIAGNOSTIC ===")
print("CRS:", data.get('crs', "EPSG:4326 (assumed)"))

primaryBld = next((f for f in data['features'] if f['properties']['is_primary']), None)
if primaryBld:
    print("Hero Building ID:", primaryBld['properties']['building_id'])
    coords = primaryBld['geometry']['coordinates'][0]
    print("First 5 Hero Coordinates:", coords[:5])
    
    minLon = min(c[0] for c in coords)
    maxLon = max(c[0] for c in coords)
    minLat = min(c[1] for c in coords)
    maxLat = max(c[1] for c in coords)
    
    sumLon = sum(c[0] for c in coords)
    sumLat = sum(c[1] for c in coords)
    
    print("Hero BBox:", {"minLon": minLon, "maxLon": maxLon, "minLat": minLat, "maxLat": maxLat})
    print("Hero Centroid (approx):", [sumLon/len(coords), sumLat/len(coords)])

print("AOI Target (from Python script): [80.205000, 13.085000]")
