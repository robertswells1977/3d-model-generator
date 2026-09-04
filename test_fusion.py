import requests
import time

FUSION_URL = "http://localhost:5000"

print("1. New Design")
requests.post(f"{FUSION_URL}/new_design", json={})
time.sleep(2)

print("2. Draw Box")
requests.post(f"{FUSION_URL}/Box", json={
    "width_value": "3.0",
    "height_value": "1.0",
    "depth_value": "3.0",
    "x_value": 0,
    "y_value": 0,
    "z_value": 0,
    "plane": "XY"
})
time.sleep(2)

print("3. Draw Cylinder")
requests.post(f"{FUSION_URL}/draw_cylinder", json={
    "radius": 1.0,
    "height": 2.0,
    "x": 0,
    "y": 0,
    "z": 0,
    "plane": "XY"
})
time.sleep(2)

print("4. Export STL")
requests.post(f"{FUSION_URL}/Export_STL", json={"Name": "/Users/robwells/sc/3d-model-generator/temp/test_export.stl"})
