"""
Phase 6E — Reports & Analytical PDF Verification Suite
"""

import sys
import uuid
import time
from pathlib import Path
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"
IMAGE_PATH = Path("images/example1.png")

def test_reports_suite():
    print("==================================================")
    print("STARTING PHASE 6E REPORTS & ANALYTICAL PDF TEST SUITE")
    print("==================================================")

    # 1. Health & Server Status
    print("\n--- 1. Checking API Health ---")
    resp = requests.get(f"{BASE_URL}/health")
    assert resp.status_code == 200, f"Health check failed: {resp.text}"
    health = resp.json()
    assert health["status"] == "ok"
    assert health["model_loaded"] is True
    print(f"Server Healthy. Model loaded: {health['model_name']}")

    # 2. Setup User A (Primary Researcher)
    print("\n--- 2. Setting Up Primary Researcher (User A) ---")
    tag_a = uuid.uuid4().hex[:8]
    email_a = f"researcher_a_{tag_a}@clarium.ai"
    pwd = "SecurePassword2026!"

    reg_a = requests.post(f"{BASE_URL}/auth/register", json={"email": email_a, "password": pwd})
    assert reg_a.status_code == 200, f"Registration of User A failed: {reg_a.text}"
    login_a = requests.post(f"{BASE_URL}/auth/login", json={"email": email_a, "password": pwd})
    assert login_a.status_code == 200, f"Login of User A failed: {login_a.text}"
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print(f"User A authenticated: {email_a}")

    # 3. Setup User B (Secondary Researcher for Access Control Test)
    print("\n--- 3. Setting Up Secondary Researcher (User B) ---")
    tag_b = uuid.uuid4().hex[:8]
    email_b = f"researcher_b_{tag_b}@clarium.ai"
    reg_b = requests.post(f"{BASE_URL}/auth/register", json={"email": email_b, "password": pwd})
    assert reg_b.status_code == 200, f"Registration of User B failed: {reg_b.text}"
    login_b = requests.post(f"{BASE_URL}/auth/login", json={"email": email_b, "password": pwd})
    assert login_b.status_code == 200, f"Login of User B failed: {login_b.text}"
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    print(f"User B authenticated: {email_b}")

    # 4. Create an Analysis Record for User A
    print("\n--- 4. Running Detection to Create Analysis Record for User A ---")
    assert IMAGE_PATH.exists(), f"Image path {IMAGE_PATH} does not exist!"
    with open(IMAGE_PATH, "rb") as f:
        detect_resp = requests.post(
            f"{BASE_URL}/detect",
            files={"file": ("example1.png", f, "image/png")},
            data={"confidence": 0.35},
            headers=headers_a,
        )
    assert detect_resp.status_code == 200, f"Detect failed: {detect_resp.text}"
    detect_data = detect_resp.json()
    analysis_id = detect_data["id"]
    total_detections = detect_data["summary"]["total_detections"]
    print(f"Analysis #{analysis_id} created with {total_detections} particles.")

    # 5. Verify Unauthenticated Report Request
    print("\n--- 5. Verifying Unauthenticated Access Rejection ---")
    no_auth_resp = requests.get(f"{BASE_URL}/analyses/{analysis_id}/report")
    assert no_auth_resp.status_code in (401, 403), f"Expected 401 or 403 for unauthenticated request, got {no_auth_resp.status_code}"
    print(f"Unauthenticated request correctly rejected with {no_auth_resp.status_code}.")

    # 6. Verify Ownership Protection (User B cannot access User A's report)
    print("\n--- 6. Verifying Cross-User Ownership Protection ---")
    forbidden_resp = requests.get(f"{BASE_URL}/analyses/{analysis_id}/report", headers=headers_b)
    assert forbidden_resp.status_code == 403, f"Expected 403 Forbidden for User B accessing User A's report, got {forbidden_resp.status_code}"
    print(f"User B correctly forbidden (403): {forbidden_resp.json().get('detail')}")

    # 7. Verify Nonexistent Analysis
    print("\n--- 7. Verifying Nonexistent Analysis Handling ---")
    not_found_resp = requests.get(f"{BASE_URL}/analyses/999999/report", headers=headers_a)
    assert not_found_resp.status_code == 404, f"Expected 404 Not Found for invalid ID, got {not_found_resp.status_code}"
    print(f"Nonexistent analysis correctly returned 404: {not_found_resp.json().get('detail')}")

    # 8. Authenticated Report Generation for User A
    print("\n--- 8. Generating Analytical PDF Report for User A ---")
    start_time = time.time()
    report_resp = requests.get(f"{BASE_URL}/analyses/{analysis_id}/report", headers=headers_a)
    gen_duration = time.time() - start_time
    assert report_resp.status_code == 200, f"Report generation failed: {report_resp.status_code} {report_resp.text}"

    content_type = report_resp.headers.get("content-type", "")
    assert "application/pdf" in content_type, f"Expected application/pdf, got {content_type}"
    print(f"Content-Type: {content_type} (Verified)")

    pdf_bytes = report_resp.content
    pdf_size = len(pdf_bytes)
    assert pdf_size > 2000, f"PDF file size suspiciously small: {pdf_size} bytes"
    assert pdf_bytes.startswith(b"%PDF-"), f"Response does not start with %PDF- header! Starts with: {pdf_bytes[:10]}"
    print(f"Valid PDF header: {pdf_bytes[:8]}")
    print(f"Generated PDF file size: {pdf_size:,} bytes ({pdf_size / 1024:.1f} KB)")
    print(f"Report generation took: {gen_duration:.3f} s (Fast programmatic generation without YOLO re-inference)")

    # Save test output
    out_dir = Path("scratch")
    out_dir.mkdir(exist_ok=True)
    out_pdf = out_dir / f"test_report_{analysis_id}.pdf"
    with open(out_pdf, "wb") as f:
        f.write(pdf_bytes)
    print(f"Saved sample PDF output to: {out_pdf}")

    # 9. Verify Regression on Existing Endpoints
    print("\n--- 9. Regression Testing Existing Phase 6D Endpoints ---")
    # History list
    hist_resp = requests.get(f"{BASE_URL}/analyses", headers=headers_a)
    assert hist_resp.status_code == 200, f"History list failed: {hist_resp.text}"
    analyses_list = hist_resp.json()
    assert any(a["id"] == analysis_id for a in analyses_list), "Created analysis missing from history list!"
    print(f"History list verified: {len(analyses_list)} records found for User A.")

    # History detail
    detail_resp = requests.get(f"{BASE_URL}/analyses/{analysis_id}", headers=headers_a)
    assert detail_resp.status_code == 200, f"History detail failed: {detail_resp.text}"
    detail_data = detail_resp.json()
    assert detail_data["id"] == analysis_id
    assert len(detail_data["detections"]) == total_detections
    print(f"History detail verified for #{analysis_id} with {len(detail_data['detections'])} detections.")

    print("\n==================================================")
    print("ALL PHASE 6E TESTS PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    try:
        test_reports_suite()
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
