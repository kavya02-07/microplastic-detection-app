import sys
import json
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = Path("images/example1.png")

def test_health():
    print("--- Testing GET /health ---")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["model_loaded"] == True

def test_detect():
    print("--- Testing POST /detect ---")
    
    if not IMAGE_PATH.exists():
        print(f"Error: Could not find image at {IMAGE_PATH.resolve()}")
        sys.exit(1)
        
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("example1.png", f, "image/png")}
        data = {"confidence": 0.40}
        
        response = requests.post(f"{BASE_URL}/detect", files=files, data=data)
        
    print(f"Status Code: {response.status_code}")
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
        sys.exit(1)
        
    result = response.json()
    summary = result.get("summary", {})
    
    print(f"Total detections: {summary.get('total_detections')}")
    print(f"Counts: {summary.get('counts_by_class')}")
    print(f"First object: {json.dumps(result.get('objects', [])[0], indent=2) if result.get('objects') else 'None'}\n")
    
    assert summary.get("total_detections") == 16, f"Expected 16 detections, got {summary.get('total_detections')}"
    print("Detection API verified successfully.")

if __name__ == "__main__":
    try:
        test_health()
        test_detect()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
