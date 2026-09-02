import re
with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

if 'selectedFeature' not in content[:1000]:
    content = re.sub(
        r'const \[traceRoute, setTraceRoute\] = useState<string>\("NONE"\);',
        'const [traceRoute, setTraceRoute] = useState<string>("NONE");\n  const [selectedFeature, setSelectedFeature] = useState<any>(null);',
        content
    )
    with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
print("Fixed selectedFeature state")
