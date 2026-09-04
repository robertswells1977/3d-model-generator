import requests

script = """
import adsk.core
def run(context):
    try:
        app = adsk.core.Application.get()
        vp = app.activeViewport
        methods = [m for m in dir(vp) if 'image' in m.lower() or 'save' in m.lower()]
        app.userInterface.messageBox("Viewport methods: " + str(methods))
    except Exception as e:
        app.userInterface.messageBox(str(e))
run(None)
"""

resp = requests.post("http://localhost:5000/run_script", json={"code": script})
print(resp.status_code, resp.text)
