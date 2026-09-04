import requests

script = """
import adsk.core
def run(context):
    try:
        app = adsk.core.Application.get()
        vp = app.activeViewport
        import inspect
        with open('/Users/robwells/sc/3d-model-generator/temp/fusion_test.txt', 'w') as f:
            f.write(vp.saveAsImageFile.__doc__)
    except Exception as e:
        pass
run(None)
"""

requests.post("http://localhost:5000/run_script", json={"code": script})
