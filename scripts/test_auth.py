import sys
import json
import requests
import uuid
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = Path("images/example1.png")

def test_auth_flow():
    print("--- Testing Phase 4 Auth Flow ---")
    
    unique_id = uuid.uuid4().hex[:8]
    test_email = f"user_{unique_id}@example.com"
    test_password = "securePassword123!"
    
    # 1. Register User
    print(f"\n1. POST /auth/register ({test_email})...")
    reg_data = {"email": test_email, "password": test_password}
    response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    
    assert response.status_code == 200, f"Register failed: {response.text}"
    user_data = response.json()
    assert user_data["email"] == test_email
    assert "password" not in user_data
    assert "password_hash" not in user_data
    print("Registration successful.")
    
    # 2. Reject Duplicate Email
    print("\n2. POST /auth/register (Duplicate)...")
    response = requests.post(f"{BASE_URL}/auth/register", json=reg_data)
    assert response.status_code == 400
    print("Duplicate email rejected correctly.")
    
    # 3. Login with incorrect credentials
    print("\n3. POST /auth/login (Wrong password)...")
    bad_login = {"email": test_email, "password": "wrongpassword"}
    response = requests.post(f"{BASE_URL}/auth/login", json=bad_login)
    assert response.status_code == 401
    print("Incorrect credentials rejected correctly.")
    
    # 4. Login successfully
    print("\n4. POST /auth/login (Correct)...")
    response = requests.post(f"{BASE_URL}/auth/login", json=reg_data)
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]
    print("Login successful. Received JWT token.")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 5. Get current user
    print("\n5. GET /auth/me ...")
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_email
    print(f"Authenticated as {response.json()['email']}")
    
    # 6. Unauthenticated access rejected
    print("\n6. POST /detect (No Auth)...")
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("example1.png", f, "image/png")}
        response = requests.post(f"{BASE_URL}/detect", files=files, data={"confidence": 0.40})
    assert response.status_code == 403 or response.status_code == 401 # HTTPBearer returns 403 by default if no header
    print("Unauthenticated access rejected correctly.")
    
    # 7. Authenticated Detection
    print("\n7. POST /detect (Authenticated)...")
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("example1.png", f, "image/png")}
        response = requests.post(f"{BASE_URL}/detect", files=files, data={"confidence": 0.40}, headers=headers)
    assert response.status_code == 200, f"Detect failed: {response.text}"
    detect_result = response.json()
    new_db_id = detect_result["id"]
    print(f"Detection successful. DB ID: {new_db_id}")
    
    # 8. User isolation
    print("\n8. Checking User Isolation...")
    # Register and login User B
    user_b_email = f"user_b_{unique_id}@example.com"
    requests.post(f"{BASE_URL}/auth/register", json={"email": user_b_email, "password": test_password})
    resp_b = requests.post(f"{BASE_URL}/auth/login", json={"email": user_b_email, "password": test_password})
    token_b = resp_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # User B tries to read User A's analysis
    response = requests.get(f"{BASE_URL}/analyses/{new_db_id}", headers=headers_b)
    assert response.status_code == 403, f"User B should not access User A's data! Got: {response.status_code}"
    
    # User B tries to list analyses (should be empty)
    response = requests.get(f"{BASE_URL}/analyses", headers=headers_b)
    assert len(response.json()) == 0, "User B should have 0 analyses."
    
    print("User isolation verified correctly.")
    print("\nALL PHASE 4 AUTH TESTS PASSED.")

if __name__ == "__main__":
    try:
        test_auth_flow()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
