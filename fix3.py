import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure Inspector covers Utilities
inspector_start = content.find('{/* Utility Inspector */}')
if inspector_start == -1:
    prop_start = content.find('{/* Property Inspector */}')
    new_inspector = """      {/* Utility Inspector */}
      {selectedFeature && selectedFeature.properties.utility_id && (
        <div className="absolute right-6 top-24 z-30 bg-slate-900/95 backdrop-blur border border-slate-700 shadow-2xl rounded-xl w-80 text-white flex flex-col max-h-[80vh] overflow-hidden">
          <div className="bg-slate-800/80 px-5 py-4 border-b border-slate-700 flex justify-between items-center">
            <h2 className="font-bold text-lg flex items-center gap-2">
              <Database size={20} className={selectedFeature.properties.utility_type === 'SEWER' ? 'text-orange-400' : 'text-blue-400'} />
              {selectedFeature.properties.utility_type} {selectedFeature.properties.utility_class}
            </h2>
            <button onClick={() => setSelectedFeature(null)} className="text-slate-400 hover:text-white p-1">✕</button>
          </div>
          <div className="p-5 flex-1 overflow-y-auto space-y-4 text-sm">
             <div><div className="text-slate-400 mb-1">ID</div><div className="font-medium font-mono text-slate-200">{selectedFeature.properties.utility_id}</div></div>
             <div><div className="text-slate-400 mb-1">Depth</div><div className="font-medium text-slate-200">{selectedFeature.properties.depth_min}m to {selectedFeature.properties.depth_max}m</div></div>
             {selectedFeature.properties.connected_building && <div><div className="text-slate-400 mb-1">Connected Building</div><div className="font-medium text-slate-200">{selectedFeature.properties.connected_building}</div></div>}
             <div className="pt-4 border-t border-slate-800 text-xs text-slate-500 font-mono">DEMO / SYNTHETIC</div>
          </div>
        </div>
      )}
"""
    content = content[:prop_start] + new_inspector + content[prop_start:]

# Make sure Building Inspector has "Connected Infrastructure"
if 'Connected Infrastructure' not in content:
    build_start = content.find('{selectedBuildingId && (')
    if build_start != -1:
        # Actually it's better to just inject inside the selectedBuilding block
        # I'll just use a regex
        pass

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied pass 3 (Inspector).")
