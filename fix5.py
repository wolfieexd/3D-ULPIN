import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

trace_buttons = """                  {/* Connected Utilities */}
                  {selectedBuildingId && (
                      <div className="mt-6 pt-6 border-t border-slate-800">
                          <h3 className="font-bold text-slate-300 mb-3 text-xs uppercase tracking-wider">Connected Infrastructure</h3>
                          <div className="flex gap-3">
                              <button onClick={() => setTraceRoute(traceRoute === 'WATER' ? 'NONE' : 'WATER')} className={`flex-1 py-2 px-3 rounded text-xs font-bold border transition-colors ${traceRoute === 'WATER' ? 'bg-cyan-600 border-cyan-500 text-white' : 'bg-slate-800 border-slate-700 text-cyan-400 hover:bg-slate-700'}`}>
                                  TRACE WATER
                              </button>
                              <button onClick={() => setTraceRoute(traceRoute === 'SEWER' ? 'NONE' : 'SEWER')} className={`flex-1 py-2 px-3 rounded text-xs font-bold border transition-colors ${traceRoute === 'SEWER' ? 'bg-orange-600 border-orange-500 text-white' : 'bg-slate-800 border-slate-700 text-orange-400 hover:bg-slate-700'}`}>
                                  TRACE SEWER
                              </button>
                          </div>
                      </div>
                  )}
"""

floor_start = content.find('{selectedFloorId && (')
if floor_start != -1 and 'TRACE WATER' not in content:
    content = content[:floor_start] + trace_buttons + content[floor_start:]

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
print("Applied pass 5 (Trace Buttons).")
