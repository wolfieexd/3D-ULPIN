import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace building coloring logic
# Find: const isPrimary = f.properties.is_primary;
# Down to: </Entity>;
pattern = re.compile(r'const isPrimary = f\.properties\.is_primary;.*?</Entity>;', re.DOTALL)

new_logic = """const isPrimary = f.properties.is_primary;
                const isMapped = f.properties.is_mapped;
                const isSelected = selectedBuildingId === f.properties.building_id;
                
                if (isSelected && (exploreFloors || (isPrimary && demoStep >= 7))) return null; 
                
                const h = f.properties.height;
                if (!validateCoordinate(h) || h <= 0) return null;
  
                const extH = Math.min(h, elevationCutoff);
                if (extH <= 0) return null;
                
                const bLon = f.geometry.coordinates[0][0][0];
                const bLat = f.geometry.coordinates[0][0][1];
                const dist = Math.sqrt((bLon - TARGET_LON)**2 + (bLat - TARGET_LAT)**2);
                
                let buildingColor, outlineColor;
                if (isSelected) {
                    buildingColor = Color.WHITE.withAlpha(0.95);
                    outlineColor = Color.DODGERBLUE;
                } else if (isPrimary) {
                    buildingColor = Color.WHITE.withAlpha(0.90);
                    outlineColor = Color.DODGERBLUE.withAlpha(0.8);
                } else if (isMapped) {
                    buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.5);
                    outlineColor = Color.CORNFLOWERBLUE.withAlpha(0.9);
                } else if (dist < 0.002) { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.20);
                    outlineColor = Color.SLATEGRAY.withAlpha(0.10);
                } else if (dist < 0.005) { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.10);
                    outlineColor = Color.SLATEGRAY.withAlpha(0.05);
                } else { 
                    buildingColor = Color.SLATEGRAY.withAlpha(0.05);
                    outlineColor = Color.TRANSPARENT;
                }
                
                return <Entity key={`b-${i}`} onClick={() => { if(isMapped) { setSelectedBuildingId(f.properties.building_id); setExploreFloors(false); setActiveFloor(null); setSelectedUnit(null); }}}>
                  <PolygonGraphics hierarchy={f._cachedHierarchy} extrudedHeight={extH} material={buildingColor} outline={outlineColor !== Color.TRANSPARENT} outlineColor={outlineColor} />
                </Entity>;"""

content, count = pattern.subn(new_logic, content)
print(f"Replaced building logic {count} times")

# Replace floor logic
pattern2 = re.compile(r'\{\(exploreFloors \|\| \(demoStep >= 7 && demoStep <= 13\) \|\| \(demoStep === 0 && selectedBuildingId === \'B001\'\)\) && primaryBuilding && floors\.features\?\.map')
new_logic2 = "{(exploreFloors || (demoStep >= 7 && demoStep <= 13) || (demoStep === 0 && selectedBuildingId)) && floors.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map"
content, count2 = pattern2.subn(new_logic2, content)
print(f"Replaced floor logic {count2} times")

# Replace unit logic
pattern3 = re.compile(r'\{\(demoStep >= 10 \|\| \(exploreFloors && activeFloor\)\) && units\.features\?\.map')
new_logic3 = "{(demoStep >= 10 || (exploreFloors && activeFloor)) && units.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map"
content, count3 = pattern3.subn(new_logic3, content)
print(f"Replaced unit logic {count3} times")


with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

