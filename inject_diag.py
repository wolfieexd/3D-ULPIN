import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

diagnostic_code = """
  // SPATIAL DIAGNOSTIC
  useEffect(() => {
    if (buildings && buildings.features && buildings.features.length > 0) {
      console.log("=== SPATIAL DIAGNOSTIC ===");
      console.log("CRS:", buildings.crs || "EPSG:4326 (assumed)");
      
      const primaryBld = buildings.features.find((f: any) => f.properties.is_primary);
      if (primaryBld) {
        console.log("Hero Building ID:", primaryBld.properties.building_id);
        const coords = primaryBld.geometry.coordinates[0];
        console.log("First 5 Hero Coordinates:", coords.slice(0, 5));
        
        let minLon = 180, maxLon = -180, minLat = 90, maxLat = -90;
        let sumLon = 0, sumLat = 0;
        coords.forEach((c: any) => {
          if (c[0] < minLon) minLon = c[0];
          if (c[0] > maxLon) maxLon = c[0];
          if (c[1] < minLat) minLat = c[1];
          if (c[1] > maxLat) maxLat = c[1];
          sumLon += c[0];
          sumLat += c[1];
        });
        console.log("Hero BBox:", { minLon, maxLon, minLat, maxLat });
        console.log("Hero Centroid (approx):", [sumLon/coords.length, sumLat/coords.length]);
      }
      
      console.log("AOI Target (from Python script):", [80.205000, 13.085000]);
    }
  }, [buildings]);
"""

# Insert right before the return statement of App component
content = content.replace("  return (", diagnostic_code + "\n  return (")

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected spatial diagnostic into App.tsx")
