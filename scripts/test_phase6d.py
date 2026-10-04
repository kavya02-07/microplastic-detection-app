import sys
import uuid
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = Path("images/example1.png")

def test_phase6d():
    print("==================================================")
    print("STARTING PHASE 6D VERIFICATION SUITE")
    print("==================================================")

    # 1. Check API Health
    print("\n--- 1. API Health & YOLO Model Check ---")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health_data = resp.json()
    assert health_data["status"] == "ok"
    assert health_data["model_loaded"] is True
    print(f"API Health: OK, Model Loaded: {health_data['model_name']}")

    # 2. Authenticate / Register Test Researcher
    print("\n--- 2. Authentication & User Creation ---")
    unique_tag = uuid.uuid4().hex[:8]
    test_email = f"researcher_6d_{unique_tag}@clarium.ai"
    test_password = "ResearchPassword2026!"

    reg_resp = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": test_email, "password": test_password},
    )
    assert reg_resp.status_code == 200, f"Registration failed: {reg_resp.text}"
    user_info = reg_resp.json()
    user_id = user_info["id"]
    print(f"Registered test user: {test_email} (ID: {user_id})")

    # Login to obtain JWT
    login_resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": test_email, "password": test_password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("JWT token successfully obtained.")

    # 3. Initial Dashboard State (Empty History for fresh user)
    print("\n--- 3. Testing Initial Dashboard State (Empty History) ---")
    history_resp = requests.get(f"{BASE_URL}/analyses", headers=headers)
    assert history_resp.status_code == 200, f"List analyses failed: {history_resp.text}"
    initial_analyses = history_resp.json()
    assert len(initial_analyses) == 0, f"Expected 0 analyses for new user, got {len(initial_analyses)}"
    print("Initial analyses list is empty (0 records). Dashboard empty state verified.")

    # 4. Perform Real Detection Inference (POST /api/v1/detect)
    print("\n--- 4. Running Real YOLO Detection (POST /api/v1/detect) ---")
    assert IMAGE_PATH.exists(), f"Sample image {IMAGE_PATH} does not exist!"

    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("example1.png", f, "image/png")}
        detect_resp = requests.post(
            f"{BASE_URL}/detect",
            files=files,
            data={"confidence": 0.40},
            headers=headers,
        )

    assert detect_resp.status_code == 200, f"Detection failed: {detect_resp.text}"
    detect_data = detect_resp.json()

    analysis_id = detect_data.get("id")
    assert analysis_id is not None, "Detection response missing database record ID!"

    summary = detect_data.get("summary", {})
    total_detections = summary.get("total_detections", 0)
    counts = summary.get("counts_by_class", {})
    avg_conf = summary.get("average_confidence", 0.0)
    inference_time = summary.get("inference_time_ms", 0.0)
    objects = detect_data.get("objects", [])

    print(f"Detection Success! Database Record ID: #{analysis_id}")
    print(f"Total Particles Detected: {total_detections}")
    print(f"Class Distribution: {counts}")
    print(f"Average Confidence: {avg_conf:.4f}")
    print(f"Inference Latency: {inference_time:.1f} ms")
    print(f"Objects returned: {len(objects)}")

    assert total_detections > 0, "Expected microplastic particles detected in example1.png!"
    assert len(objects) == total_detections, "Mismatch between objects array and total_detections count!"

    # Verify object structure
    first_obj = objects[0]
    for key in ["class_id", "class_name", "confidence", "bbox", "width", "height", "area", "aspect_ratio"]:
        assert key in first_obj, f"Object missing required field: {key}"
    print("Detected objects schema validated successfully.")

    # 5. Verify History List (GET /api/v1/analyses)
    print("\n--- 5. Verifying History List (GET /api/v1/analyses) ---")
    history_after = requests.get(f"{BASE_URL}/analyses", headers=headers)
    assert history_after.status_code == 200, f"List analyses failed: {history_after.text}"
    analyses_list = history_after.json()
    assert len(analyses_list) == 1, f"Expected 1 analysis in history, got {len(analyses_list)}"

    hist_item = analyses_list[0]
    assert hist_item["id"] == analysis_id
    assert hist_item["original_filename"] == "example1.png"
    assert hist_item["total_detections"] == total_detections
    assert abs(hist_item["average_confidence"] - avg_conf) < 1e-4
    assert hist_item["created_at"] is not None
    print("History record correctly matches the detection run.")

    # 6. Verify Historical Detail (GET /api/v1/analyses/{id}) - No YOLO rerun
    print("\n--- 6. Verifying Historical Detail (GET /api/v1/analyses/{id}) ---")
    detail_resp = requests.get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers)
    assert detail_resp.status_code == 200, f"Get detail failed: {detail_resp.text}"
    detail_data = detail_resp.json()

    assert detail_data["id"] == analysis_id
    assert detail_data["original_filename"] == "example1.png"
    assert detail_data["total_detections"] == total_detections
    assert "detections" in detail_data, "Historical detail missing 'detections' list!"
    assert len(detail_data["detections"]) == total_detections, "Mismatch in detections count!"

    # Verify detection geometry in saved record
    first_det = detail_data["detections"][0]
    for det_key in ["id", "class_name", "confidence", "width", "height", "area", "aspect_ratio"]:
        assert det_key in first_det, f"Saved detection missing field: {det_key}"
    print("Historical analysis detail loaded from SQLite database successfully without re-inference.")

    # 7. Verify Dashboard Calculation Correctness
    print("\n--- 7. Verifying Dashboard Metrics Calculation ---")
    # Total Analyses
    calc_total_analyses = len(analyses_list)
    # Total Particles
    calc_total_particles = sum(a["total_detections"] for a in analyses_list)
    # Weighted Average Confidence
    calc_weighted_conf = sum(a["average_confidence"] * a["total_detections"] for a in analyses_list) / calc_total_particles

    assert calc_total_analyses == 1
    assert calc_total_particles == total_detections
    assert abs(calc_weighted_conf - avg_conf) < 1e-4
    print(f"Calculated Dashboard Stats: Analyses={calc_total_analyses}, Particles={calc_total_particles}, AvgConf={calc_weighted_conf*100:.1f}%")

    # 8. Verify User Isolation for History & Detail
    print("\n--- 8. Verifying User Isolation ---")
    user_b_email = f"user_b_{unique_tag}@clarium.ai"
    requests.post(f"{BASE_URL}/auth/register", json={"email": user_b_email, "password": test_password})
    b_login = requests.post(f"{BASE_URL}/auth/login", json={"email": user_b_email, "password": test_password})
    token_b = b_login.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B lists analyses -> must be 0
    b_hist = requests.get(f"{BASE_URL}/analyses", headers=headers_b)
    assert len(b_hist.json()) == 0, "User B saw User A's analyses in list!"

    # User B accesses User A's analysis directly -> must return 403
    b_detail = requests.get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers_b)
    assert b_detail.status_code == 403, f"User B accessed User A's analysis! Status: {b_detail.status_code}"
    print("User isolation verified: User B cannot access User A's analysis record.")

    # 9. Verify Unauthenticated Protection
    print("\n--- 9. Verifying Protected Routes Reject Unauthenticated Requests ---")
    unauth_hist = requests.get(f"{BASE_URL}/analyses")
    assert unauth_hist.status_code in [401, 403], f"Unauthenticated request allowed: {unauth_hist.status_code}"
    unauth_det = requests.get(f"{BASE_URL}/analyses/{analysis_id}")
    assert unauth_det.status_code in [401, 403], f"Unauthenticated request allowed: {unauth_det.status_code}"
    print("Protected routes rejected unauthenticated requests as expected.")

    print("\n==================================================")
    print("PHASE 6D FULL VERIFICATION COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    try:
        test_phase6d()
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
