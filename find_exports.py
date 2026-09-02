with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'export default App;' in line:
            print(f"Line {i+1}")
