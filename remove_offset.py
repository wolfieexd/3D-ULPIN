import re

with open('scripts/generate_demo_data_v5.py', 'r') as f:
    content = f.read()

# Remove the manual offset
old_coords = """            lon, lat = p.strip().split(' ')
            # Apply OSM datum shift for Chennai Open Buildings
            lon = float(lon) - 0.00008
            lat = float(lat) - 0.00010
            coords.append([lon, lat])"""

new_coords = """            lon, lat = p.strip().split(' ')
            coords.append([float(lon), float(lat)])"""

content = content.replace(old_coords, new_coords)

with open('scripts/generate_demo_data_v5.py', 'w') as f:
    f.write(content)
print("Removed manual offset from generator.")
