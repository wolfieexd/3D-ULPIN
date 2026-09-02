import re

with open('frontend/src/App.tsx', 'rb') as f:
    content = f.read().decode('utf-8')

# 1. Update building mapping logic
old_bld_logic = """                const isPrimary = f.properties.is_primary;
                if (isPrimary && (exploreFloors || demoStep >= 7)) return null; 
                
                const h = f.properties.height;
                if (!validateCoordinate(h) || h <= 0) return null;
  
                const extH = Math.min(h, elevationCutoff);
                if (extH <= 0) return null;
                
                const bLon = f.geometry.coordinates[0][0][0];
                const bLat = f.geometry.coordinates[0][0][1];
                const dist = Math.sqrt((bLon - TARGET_LON)**2 + (bLat - TARGET_LAT)**2);
                
                let buildingColor, outlineColor;
                if (isPrimary) {
                    buildingColor = Color.WHITE.withAlpha(0.95);
                    outlineColor = Color.DODGERBLUE;
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
                
                return <Entity key={`b-${i}`} onClick={() => { if(isPrimary) { setSelectedBuildingId(f.properties.building_id); setExploreFloors(false); setActiveFloor(null); setSelectedUnit(null); }}}>
                  <PolygonGraphics hierarchy={f._cachedHierarchy} extrudedHeight={extH} material={buildingColor} outline={outlineColor !== Color.TRANSPARENT} outlineColor={outlineColor} />
                </Entity>;"""

new_bld_logic = """                const isPrimary = f.properties.is_primary;
                const isMapped = f.properties.is_mapped;
                const isSelected = selectedBuildingId === f.properties.building_id;
                
                // If a building is selected and we are exploring floors, hide the solid building block
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
                    buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.7);
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

content = content.replace(old_bld_logic, new_bld_logic)

# 2. Update floors filtering
old_floor_logic = "{(exploreFloors || (demoStep >= 7 && demoStep <= 13) || (demoStep === 0 && selectedBuildingId === 'B001')) && primaryBuilding && floors.features?.map"
new_floor_logic = "{(exploreFloors || (demoStep >= 7 && demoStep <= 13) || (demoStep === 0 && selectedBuildingId)) && floors.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map"
content = content.replace(old_floor_logic, new_floor_logic)

# 3. Update units filtering
old_unit_logic = "{(demoStep >= 10 || (exploreFloors && activeFloor)) && units.features?.map((f: any, i: number) => {"
new_unit_logic = "{(demoStep >= 10 || (exploreFloors && activeFloor)) && units.features?.filter((f: any) => f.properties.building_id === (demoStep >= 7 && demoStep <= 13 ? 'B001' : selectedBuildingId)).map((f: any, i: number) => {"
content = content.replace(old_unit_logic, new_unit_logic)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated App.tsx")
