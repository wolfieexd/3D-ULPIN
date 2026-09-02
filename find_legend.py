with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'Underground Legend' in line:
            for j in range(i-5, i+30):
                print(f"{j+1}: {f.readlines()[j].rstrip() if j < len(f.readlines()) else ''}")
            break
