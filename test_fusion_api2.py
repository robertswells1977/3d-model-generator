import requests

script = """
import adsk.core
def run(context):
    try:
        app = adsk.core.Application.get()
        vp = app.activeViewport
        methods = [m for m in dir(vp) if 'image' in m.lower() or 'save' in m.lower()]
        
        with open('/Users/robwells/sc/3d-model-generator/temp/fusion_test.txt', 'w') as f:
            f.write("Viewport methods: " + str(methods))
    except Exception as e:
        with open('/Users/robwells/sc/3d-model-generator/temp/fusion_test.txt', 'w') as f:
            f.write(str(e))
run(None)
"""

requests.post("http://localhost:5000/run_script", json={"code": script})
