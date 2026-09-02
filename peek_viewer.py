with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

start_utils = content.find('{(showUnderground || demoStep >= 14) && utilities.features?.map(')
if start_utils != -1:
    end_utils = content.find('</Viewer>', start_utils)
    if end_utils != -1:
        # We also have conflicts in there:
        # Let's peek what's before </Viewer>
        print(content[end_utils-1000:end_utils])
