with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('{(showUnderground || demoStep >= 14) && utilities.features?.map((f: any, i: number) => {')
print(content[start_idx:start_idx+1000])
