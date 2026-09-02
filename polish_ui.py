import re, os
path = 'frontend/src/App.tsx'
with open(path, 'r', encoding='utf-8') as f:
    txt = f.read()

# 1. Conflict label: reduce font size, remove background, adjust offset
conflict_label_pattern = r'(<LabelGraphics[^>]*font=\"bold 12px monospace\"[^>]*)(backgroundColor={Color\.RED.withAlpha\(0\.9\)})?([^>]*pixelOffset={new Cartesian2\(120, -100\)})'
conflict_label_repl = r'\1font=\"bold 10px monospace\" fillColor={Color.WHITE} showBackground={false}\3'
txt = re.sub(conflict_label_pattern, conflict_label_repl, txt)

# add a thin leader line from sphere to label (just before label entity)
leader_pattern = r'(\s*<Entity position={Cartesian3.fromDegrees\(p\[0\], p\[1\], -1\.75\)}>\s*\n\s*<EllipsoidGraphics[^>]+/>\s*\n\s*</Entity>\s*\n\s*)'
leader_repl = r"\1                <Entity polyline={{ positions: Cartesian3.fromDegreesArray([p[0], p[1], p[0], p[1]]), width: 1, material: Color.WHITE.withAlpha(0.6) }} />\n"
txt = re.sub(leader_pattern, leader_repl, txt)

# 2. Z-axis: smaller font and move offset (increase pixelOffset X to -20)
txt = re.sub(r'font=\"bold 10px monospace\"', 'font="bold 9px monospace"', txt)
txt = re.sub(r'pixelOffset={new Cartesian2\(mark.offset, 0\)}', 'pixelOffset={new Cartesian2(mark.offset-15, 0)}', txt)

# 3. Add Utility Depth card near Z-axis after Z-axis rendering
zaxis_end_pattern = r'(</React\.Fragment>\s*\)\s*\)\s*\})'  # after z-axis fragment closing? We'll locate the closing of z-axis block
# Simplify: find the block where Z-axis is rendered and insert after it.
insert_point = txt.find('/* Z-Axis Visualization */')
if insert_point != -1:
    # Find end of that block (after the React.Fragment for zmarks)
    end_idx = txt.find('</React.Fragment>', insert_point)
    if end_idx != -1:
        insertion = '''
                {/* Utility Depth Card */}
                <Entity position={Cartesian3.fromDegrees(axisLon - 0.00002, axisLat, -2.0)}>
                    <LabelGraphics
                        text={"UTILITY DEPTH\\nSEWER -2.0m → -1.0m\\nWATER -2.5m → -1.5m"}
                        font="bold 9px monospace"
                        fillColor={Color.WHITE}
                        showBackground={true}
                        backgroundColor={Color.BLACK.withAlpha(0.6)}
                        pixelOffset={new Cartesian2(-80, 20)}
                        disableDepthTestDistance={Number.POSITIVE_INFINITY}
                    />
                </Entity>
'''        
        txt = txt[:end_idx] + insertion + txt[end_idx:]

# 4. Building selection outline cyan already set earlier, ensure outlineColor cyan when selected
# (found earlier replacement) ensure outlineColor line includes cyan
bldg_outline_pattern = r'outlineColor = showUnderground \? Color\.CYAN : Color\.DODGERBLUE;'
# already set

# 5. Legend size reduction: change class names for width and text size
txt = re.sub(r'className="([^"]*?)"', lambda m: 'className="' + m.group(1).replace('p-5', 'p-3').replace('text-sm', 'text-xs') + '"', txt)

# 6. Left sidebar status card: locate Detect Conflicts button block and insert after
detect_conflicts_pattern = r'(\{\s*<button[^>]*>Detect Conflicts</button>\s*\})'
status_card = '''
                <div className="mt-4 p-3 bg-slate-800/80 border border-slate-700 rounded text-xs text-slate-200">
                    <div className="font-bold mb-1">UNDERGROUND MODE</div>
                    <div>Depth<br/>-5m → 0m</div>
                    <div>Utilities<br/>62</div>
                    <div>Conflict<br/>1 DETECTED</div>
                </div>
'''
txt = re.sub(detect_conflicts_pattern, r'\1' + status_card, txt)

# 7. Right inspector hierarchy: locate inspector container and add hierarchy lines
inspector_pattern = r'(<h2 className="font-bold text-lg flex items-center gap-2">[^<]+</h2>)'
hierarchy_html = '''
                    <div className="mt-2 text-xs text-slate-400">
                        <div>PARCEL<br/>P000001</div>
                        <div className="ml-2">↓</div>
                        <div>BUILDING<br/>B001</div>
                        <div className="ml-2">↓</div>
                        <div>FLOORS<br/>4</div>
                        <div className="ml-2">↓</div>
                        <div>3D PROPERTY UNITS<br/>16</div>
                    </div>
'''
txt = re.sub(inspector_pattern, r'\1' + hierarchy_html, txt)

# 8. Bottom status bar readability: find status bar and adjust text
txt = re.sub(r'className="([^"]*?)"', lambda m: 'className="' + m.group(1).replace('text-sm', 'text-xs') + '"', txt)

with open(path, 'w', encoding='utf-8') as f:
    f.write(txt)
print('Applied final UI polish')
