with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()
start_idx = content.find('{(showUnderground || demoStep >= 14) && utilities.features?.map((f: any, i: number) => {')
end_idx = content.find('{showConflicts && (')
print("start:", start_idx, "end:", end_idx)
