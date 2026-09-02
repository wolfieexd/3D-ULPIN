import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. IMPORTS
content = re.sub(
    r'import \{ Cartesian3, Color, Math as CesiumMath, BoundingSphere, HeadingPitchRange, UrlTemplateImageryProvider, Cartesian2, GlobeTranslucency \} from "cesium";',
    'import { Cartesian3, Color, Math as CesiumMath, BoundingSphere, HeadingPitchRange, UrlTemplateImageryProvider, Cartesian2, GlobeTranslucency, PolylineGlowMaterialProperty, PolylineDashMaterialProperty, Math } from "cesium";',
    content
)

# 2. STATE
if 'traceRoute' not in content:
    content = re.sub(
        r'const \[demoStep, setDemoStep\] = useState<number>\(0\);',
        'const [demoStep, setDemoStep] = useState<number>(0);\n  const [traceRoute, setTraceRoute] = useState<string>("NONE");',
        content
    )

# 3. VALIDATION FIX
val_old = """
        if (utilRes.data && utilRes.data.features) {
            report.util = utilRes.data.features.length;
            utilRes.data.features.forEach((f: any) => {
               const coords = f.geometry.coordinates.flat();
               if (coords.length >= 4 && validateCoordinate(f.properties.z_max)) {
                  report.utilValid++;
                  f._cachedPositions = Cartesian3.fromDegreesArrayHeights([
                      coords[0], coords[1], f.properties.z_max,
                      coords[2], coords[3], f.properties.z_max
                  ]);
               } else {
                   console.warn(`[Geometry Validation] Skipping Utility ${f.properties.utility_id}`);
               }
            });
        }
"""
val_new = """
        if (utilRes.data && utilRes.data.features) {
            report.util = utilRes.data.features.length;
            utilRes.data.features.forEach((f: any) => {
               if (f.geometry && f.geometry.type === 'LineString' && f.geometry.coordinates && f.geometry.coordinates.length >= 2) {
                   const props = f.properties || {};
                   if (props.depth_min !== undefined && props.depth_max !== undefined && props.utility_id) {
                       report.utilValid++;
                   } else {
                       console.warn(`[Geometry Validation] Skipping Utility ${f.properties.utility_id} - missing properties`);
                   }
               } else {
                   console.warn(`[Geometry Validation] Skipping Utility ${f.properties?.utility_id} - invalid geometry`);
               }
            });
        }
"""
# Use regex to replace the validation block robustly since indentation might vary
val_pattern = r'if\s*\(utilRes\.data\s*&&\s*utilRes\.data\.features\)\s*\{\s*report\.util\s*=\s*utilRes\.data\.features\.length;\s*utilRes\.data\.features\.forEach\(\(f:\s*any\)\s*=>\s*\{\s*const\s*coords\s*=\s*f\.geometry\.coordinates\.flat\(\);\s*if\s*\(coords\.length\s*>=\s*4\s*&&\s*validateCoordinate\(f\.properties\.z_max\)\)\s*\{\s*report\.utilValid\+\+;[\s\S]*?\}\s*else\s*\{\s*console\.warn\(`\[Geometry\s*Validation\]\s*Skipping\s*Utility\s*\$\{f\.properties\.utility_id\}`\);\s*\}\s*\}\);\s*\}'
content = re.sub(val_pattern, val_new.strip(), content)

# 4. OPACITY FOR BUILDINGS
bld_render_pattern = r'const isPrimary = f\.properties\.is_primary;\s*let buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.02\) : Color\.SLATEGRAY\.withAlpha\(0\.05\);\s*let outlineColor = Color\.TRANSPARENT;\s*if \(isPrimary\) \{\s*buildingColor = showUnderground \? Color\.CORNFLOWERBLUE\.withAlpha\(0\.2\) : Color\.CORNFLOWERBLUE\.withAlpha\(0\.5\);\s*outlineColor = Color\.CORNFLOWERBLUE\.withAlpha\(0\.9\);\s*\} else if \(dist < 0\.002\) \{ \s*buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.05\) : Color\.SLATEGRAY\.withAlpha\(0\.20\);\s*outlineColor = Color\.SLATEGRAY\.withAlpha\(0\.10\);\s*\} else if \(dist < 0\.005\) \{ \s*buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.02\) : Color\.SLATEGRAY\.withAlpha\(0\.10\);\s*outlineColor = Color\.SLATEGRAY\.withAlpha\(0\.05\);\s*\}'
bld_render_new = """const isPrimary = f.properties.is_primary;
                  const isContext = f.properties.is_mapped;
                  let buildingColor = Color.SLATEGRAY.withAlpha(0.05);
                  let outlineColor = Color.TRANSPARENT;
                  
                  if (showUnderground || elevationCutoff < -0.1) {
                      if (isPrimary) {
                          buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.3);
                          outlineColor = Color.CORNFLOWERBLUE.withAlpha(0.5);
                      } else if (isContext) {
                          buildingColor = Color.SLATEGRAY.withAlpha(0.15);
                          outlineColor = Color.SLATEGRAY.withAlpha(0.3);
                      } else {
                          buildingColor = Color.SLATEGRAY.withAlpha(0.02);
                      }
                  } else {
                      if (isPrimary) {
                          buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.5);
                          outlineColor = Color.CORNFLOWERBLUE.withAlpha(0.9);
                      } else if (dist < 0.002) { 
                          buildingColor = Color.SLATEGRAY.withAlpha(0.20);
                          outlineColor = Color.SLATEGRAY.withAlpha(0.10);
                      } else if (dist < 0.005) { 
                          buildingColor = Color.SLATEGRAY.withAlpha(0.10);
                          outlineColor = Color.SLATEGRAY.withAlpha(0.05);
                      }
                  }"""
content = re.sub(bld_render_pattern, bld_render_new, content)

# 5. UTILITIES RENDER BLOCK
utils_start = content.find('{/* 3D Utilities Data */}')
utils_end = content.find('{/* 3D Spatial Conflicts */}')
if utils_start != -1 and utils_end != -1:
    new_utils = """{/* 3D Utilities Data */}
            {utilities && utilities.features && utilities.features.map((u: any, i: number) => {
                if (!showUnderground && demoStep < 14 && elevationCutoff >= 0) return null;
                
                const props = u.properties;
                const coords = u.geometry.coordinates;
                if (!coords || coords.length < 2) return null;

                const isSewer = props.utility_type === 'SEWER';
                const isMain = props.utility_class === 'MAIN';
                
                // Z depth mapping
                const z1 = isMain ? (props.depth_max + props.depth_min)/2 : (isSewer ? -1.0 : -1.5);
                const z2 = isMain ? (props.depth_max + props.depth_min)/2 : (isSewer ? -1.5 : -2.5);
                
                let material: any = isSewer ? Color.ORANGERED : Color.CYAN;
                let width = isMain ? 10 : 5;
                
                // Tracing logic
                const isTraced = traceRoute !== "NONE" && (
                    (traceRoute === "WATER" && !isSewer) || 
                    (traceRoute === "SEWER" && isSewer)
                );
                
                if (isMain) {
                    material = new PolylineGlowMaterialProperty({
                        glowPower: 0.3,
                        taperPower: 1.0,
                        color: isSewer ? Color.ORANGERED : Color.CYAN
                    });
                }
                
                if (isTraced) {
                    material = new PolylineDashMaterialProperty({
                        color: Color.YELLOW,
                        gapColor: Color.TRANSPARENT,
                        dashLength: 16.0,
                        dashPattern: 255.0
                    });
                    width += 4;
                } else if (traceRoute !== "NONE") {
                    material = Color.GRAY.withAlpha(0.1);
                }
                
                return (
                    <Entity 
                        key={`util-${i}`}
                        onClick={() => setSelectedFeature(u)}
                        description={props.utility_id}
                    >
                        <PolylineGraphics
                            positions={Cartesian3.fromDegreesArrayHeights([
                                coords[0][0], coords[0][1], z1,
                                coords[1][0], coords[1][1], z2
                            ])}
                            width={width}
                            material={material}
                        />
                        {!isMain && (
                            <Entity position={Cartesian3.fromDegrees(coords[1][0], coords[1][1], z2)}>
                                <EllipsoidGraphics radii={new Cartesian3(0.5, 0.5, 0.5)} material={Color.YELLOW} />
                            </Entity>
                        )}
                    </Entity>
                );
            })}
            """
    content = content[:utils_start] + new_utils + content[utils_end:]

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Pass 1 applied.")
