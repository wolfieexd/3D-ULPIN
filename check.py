import json
with open('frontend/public/data/buildings.geojson', 'r') as f:
    data = json.load(f)
for f in data['features'][:5]:
    print(f['properties']['building_id'], f['geometry']['coordinates'][0][:3])
