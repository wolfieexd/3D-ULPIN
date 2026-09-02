import csv
import math

CSV_PATH = r"D:\SIH 2026\data\raw\google\open_buildings_v3_chennai.csv"
TARGET_LON = 80.205000
TARGET_LAT = 13.085000

good_buildings = []
with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        area = float(row['area_in_meters'])
        if 150 < area < 350:
            lon = float(row['longitude'])
            lat = float(row['latitude'])
            dist = math.sqrt((lon - TARGET_LON)**2 + (lat - TARGET_LAT)**2)
            good_buildings.append({'dist': dist, 'area': area})

good_buildings.sort(key=lambda x: x['dist'])
print("Found", len(good_buildings), "perfectly sized buildings.")
for b in good_buildings[:10]:
    print(f"Dist: {b['dist']:.5f}, Area: {b['area']:.1f}")
