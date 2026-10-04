import sys
import json
import requests
import uuid
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = Path("images/example1.png")

def test_database_flow():
    print("--- Testing Phase 3 Database Flow (Updated for Auth) ---")
    
    # Register and login a user for the tests
    test_email = f"dbtest_{uuid.uuid4().hex[:8]}@example.com"
    requests.post(f"{BASE_URL}/auth/register", json={"email": test_email, "password": "pw"})
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": test_email, "password": "pw"})
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Perform a detection which should now save to the DB
    print("\n1. POST /detect (uploading image)...")
    if not IMAGE_PATH.exists():
        print(f"Error: Could not find image at {IMAGE_PATH.resolve()}")
        sys.exit(1)
        
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("example1.png", f, "image/png")}
        data = {"confidence": 0.40}
        response = requests.post(f"{BASE_URL}/detect", files=files, data=data, headers=headers)
        
    if response.status_code != 200:
        print(f"Error Response: {response.text}")
        sys.exit(1)
        
    detect_result = response.json()
    new_db_id = detect_result.get("id")
    print(f"Detection successful. DB ID returned: {new_db_id}")
    assert new_db_id is not None, "API did not return a database record ID"
    assert detect_result["summary"]["total_detections"] > 0
    
    # 2. Get list of analyses
    print("\n2. GET /analyses ...")
    response = requests.get(f"{BASE_URL}/analyses", headers=headers)
    assert response.status_code == 200
    analyses = response.json()
    print(f"Found {len(analyses)} analyses in the database.")
    assert len(analyses) >= 1
    
    # 3. Get specific analysis with its individual detections
    print(f"\n3. GET /analyses/{new_db_id} ...")
    response = requests.get(f"{BASE_URL}/analyses/{new_db_id}", headers=headers)
    assert response.status_code == 200
    
    analysis_detail = response.json()
    print(f"Successfully retrieved Analysis #{analysis_detail['id']}")
    print(f"Original filename: {analysis_detail['original_filename']}")
    print(f"Confidence threshold used: {analysis_detail['confidence_threshold']}")
    
    saved_detections = analysis_detail.get("detections", [])
    print(f"Individual detections saved: {len(saved_detections)}")
    
    assert len(saved_detections) == detect_result["summary"]["total_detections"], \
        "Mismatch between detected objects and saved objects"
        
    print("\nFirst saved detection detail:")
    print(json.dumps(saved_detections[0], indent=2))
    
    print("\nALL PHASE 3 DATABASE TESTS PASSED.")

if __name__ == "__main__":
    try:
        test_database_flow()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
