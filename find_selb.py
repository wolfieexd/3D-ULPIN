with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('{selBuilding.properties.height')
print(content[max(0, idx-100):idx+500])
