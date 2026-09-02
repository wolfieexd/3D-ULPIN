import re

with open('frontend/src/App.tsx', 'rb') as f:
    content = f.read()

content = content.replace(b'viewer.scene.skyAtmosphere.show = false;\r\n      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;\r\n      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;', b'viewer.scene.skyAtmosphere.show = false;\r\n      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;')

with open('frontend/src/App.tsx', 'wb') as f:
    f.write(content)
