import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

conflict_start = content.find('{/* 3D Spatial Conflicts */}')
conflict_end = content.find('{/* End Conflicts */}')
if conflict_start != -1 and conflict_end != -1:
    new_conflicts = """{/* 3D Spatial Conflicts */}
            {conflicts && conflicts.features && conflicts.features.map((c: any, i: number) => {
                if (!showUnderground && demoStep < 14 && elevationCutoff >= 0) return null;
                const p = c.geometry.coordinates;
                return (
                    <React.Fragment key={`conflict-${i}`}>
                        <Entity position={Cartesian3.fromDegrees(p[0], p[1], -1.75)}>
                            <EllipsoidGraphics radii={new Cartesian3(2.5, 2.5, 2.5)} material={Color.RED.withAlpha(0.9)} outline={true} outlineColor={Color.ORANGERED} />
                        </Entity>
                        <Entity position={Cartesian3.fromDegrees(p[0], p[1], -1.75)}>
                            <LabelGraphics text={`⚠ 3D SPATIAL CONFLICT\\nWATER × SEWER\\nZ OVERLAP: -2.0m → -1.5m`} font="bold 12px monospace" fillColor={Color.WHITE} showBackground={true} backgroundColor={Color.RED.withAlpha(0.9)} pixelOffset={new Cartesian2(100, -80)} disableDepthTestDistance={Number.POSITIVE_INFINITY} />
                        </Entity>
                    </React.Fragment>
                );
            })}
            """
    content = content[:conflict_start] + new_conflicts + content[conflict_end:]
    
with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied pass 2 (Conflicts).")
