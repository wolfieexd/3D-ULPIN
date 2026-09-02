import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

legend = """      {/* Underground Legend */}
      {showUnderground && (
        <div className="absolute bottom-6 left-6 z-30 bg-slate-900/95 backdrop-blur border border-slate-700 shadow-2xl p-5 rounded-xl text-white min-w-[260px]">
          <h3 className="font-bold text-sm tracking-wider text-slate-400 mb-3 uppercase">Underground Network</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3"><div className="w-2 h-2 rounded-full bg-yellow-400 shadow-[0_0_8px_rgba(250,204,21,0.8)]"></div><span>Building Connection</span></div>
            <div className="flex items-center gap-3"><div className="w-8 h-1.5 bg-cyan-500 rounded"></div><span>Water Main</span></div>
            <div className="flex items-center gap-3"><div className="w-8 h-0.5 bg-cyan-400 rounded"></div><span>Water Service</span></div>
            <div className="flex items-center gap-3"><div className="w-8 h-1.5 bg-orange-600 rounded"></div><span>Sewer Main</span></div>
            <div className="flex items-center gap-3"><div className="w-8 h-0.5 bg-orange-400 rounded"></div><span>Sewer Service</span></div>
            <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-red-600"></div><span>Spatial Conflict</span></div>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-800 text-xs text-slate-500 font-mono">
            DATA<br/>DEMO / SYNTHETIC
          </div>
        </div>
      )}
"""
prop_start = content.find('{/* Property Inspector */}')
if prop_start != -1:
    content = content[:prop_start] + legend + content[prop_start:]

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied pass 4 (Legend).")
