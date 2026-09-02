import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Imports
content = re.sub(
    r'import \{ Cartesian3, Color, Math as CesiumMath, BoundingSphere, HeadingPitchRange, UrlTemplateImageryProvider, Cartesian2, GlobeTranslucency \} from "cesium";',
    'import { Cartesian3, Color, Math as CesiumMath, BoundingSphere, HeadingPitchRange, UrlTemplateImageryProvider, Cartesian2, GlobeTranslucency, PolylineGlowMaterialProperty, PolylineDashMaterialProperty, Math } from "cesium";',
    content
)

# 2. Add traceRoute state
content = re.sub(
    r'const \[demoStep, setDemoStep\] = useState<number>\(0\);',
    'const [demoStep, setDemoStep] = useState<number>(0);\n  const [traceRoute, setTraceRoute] = useState<string>("NONE");',
    content
)

# 3. Fix Utilities validation logic
val_pattern = r'''\s*const coords = f\.geometry\.coordinates\.flat\(\);\s*if \(coords\.length >= 4 && validateCoordinate\(f\.properties\.z_max\)\) \{\s*report\.utilValid\+\+;\s*f\._cachedPositions = Cartesian3\.fromDegreesArrayHeights\(\[\s*coords\[0\], coords\[1\], f\.properties\.z_max,\s*coords\[2\], coords\[3\], f\.properties\.z_max\s*\]\);\s*\} else \{\s*console\.warn\(\`\[Geometry Validation\] Skipping Utility \$\{f\.properties\.utility_id\}\`\);\s*\}'''

val_new = """               if (f.geometry.type === 'LineString' && f.geometry.coordinates.length >= 2) {
                   const props = f.properties;
                   if (props.depth_min !== undefined && props.depth_max !== undefined && props.utility_id) {
                       report.utilValid++;
                   } else {
                       console.warn(`[Geometry Validation] Missing depth properties on utility ${props.utility_id}`);
                   }
               } else {
                   console.warn(`[Geometry Validation] Invalid LineString geometry on utility`);
               }"""
content = re.sub(val_pattern, val_new, content)

# 4. Utilities Rendering Block Overhaul
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
                
                // Actual Z depths
                const z = (props.depth_min + props.depth_max) / 2.0;
                
                let material: any = isSewer ? Color.ORANGERED : Color.DEEPSKYBLUE;
                let width = isMain ? 10 : 5;
                
                // Tracing logic
                const isTraced = traceRoute !== "NONE" && (
                    (traceRoute === "WATER" && !isSewer) || 
                    (traceRoute === "SEWER" && isSewer)
                );
                
                if (isMain) {
                    material = new PolylineGlowMaterialProperty({
                        glowPower: 0.25,
                        taperPower: 1,
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
                                coords[0][0], coords[0][1], z,
                                coords[1][0], coords[1][1], z
                            ])}
                            width={width}
                            material={material}
                        />
                        {/* Connection Node at building edge */}
                        {!isMain && (
                            <Entity position={Cartesian3.fromDegrees(coords[1][0], coords[1][1], z)}>
                                <EllipsoidGraphics 
                                    radii={new Cartesian3(0.5, 0.5, 0.5)} 
                                    material={Color.YELLOW} 
                                />
                                {isTraced && (
                                    <LabelGraphics text="NODE" font="10px sans-serif" fillColor={Color.WHITE} pixelOffset={new Cartesian2(10, -10)} />
                                )}
                            </Entity>
                        )}
                    </Entity>
                );
            })}
            """
    content = content[:utils_start] + new_utils + content[utils_end:]

# 5. Building Rendering Opacity
bld_old = r'''const isPrimary = f\.properties\.is_primary;\s*let buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.02\) : Color\.SLATEGRAY\.withAlpha\(0\.05\);\s*let outlineColor = Color\.TRANSPARENT;\s*if \(isPrimary\) \{\s*buildingColor = showUnderground \? Color\.CORNFLOWERBLUE\.withAlpha\(0\.2\) : Color\.CORNFLOWERBLUE\.withAlpha\(0\.5\);\s*outlineColor = Color\.CORNFLOWERBLUE\.withAlpha\(0\.9\);\s*\} else if \(dist < 0\.002\) \{ \s*buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.05\) : Color\.SLATEGRAY\.withAlpha\(0\.20\);\s*outlineColor = Color\.SLATEGRAY\.withAlpha\(0\.10\);\s*\} else if \(dist < 0\.005\) \{ \s*buildingColor = showUnderground \? Color\.SLATEGRAY\.withAlpha\(0\.02\) : Color\.SLATEGRAY\.withAlpha\(0\.10\);\s*outlineColor = Color\.SLATEGRAY\.withAlpha\(0\.05\);\s*\}'''
bld_new = """const isPrimary = f.properties.is_primary;
                  const isContext = f.properties.is_mapped;
                  let buildingColor = Color.SLATEGRAY.withAlpha(0.05);
                  let outlineColor = Color.TRANSPARENT;
                  
                  if (showUnderground || elevationCutoff < -0.1) {
                      // Underground Mode Hierarchy
                      if (isPrimary) {
                          buildingColor = Color.CORNFLOWERBLUE.withAlpha(0.3);
                          outlineColor = Color.CORNFLOWERBLUE.withAlpha(0.6);
                      } else if (isContext) {
                          buildingColor = Color.SLATEGRAY.withAlpha(0.15);
                          outlineColor = Color.SLATEGRAY.withAlpha(0.3);
                      } else {
                          buildingColor = Color.SLATEGRAY.withAlpha(0.02);
                      }
                  } else {
                      // Normal Mode
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
content = re.sub(bld_old, bld_new, content)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied pass 1.")
