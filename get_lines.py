with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()
for i in range(1380, 1400):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}")
