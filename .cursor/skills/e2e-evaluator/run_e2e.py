import os
import sys
import json
import urllib.request
import subprocess
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from fastapi.testclient import TestClient
from app import app

def main():
    print("=== 1. E2E API ENDPOINT VALIDATION (TestClient) ===")
    client = TestClient(app)

    res_config = client.get("/api/config")
    if res_config.status_code != 200:
        print(f"[FAIL] GET /api/config returned status {res_config.status_code}")
        sys.exit(1)
    data_config = res_config.json()
    print("[OK] Config Endpoint returned models:", len(data_config.get("models", [])))

    res_bad = client.post("/api/expand", json={
        "sentence_with_blank": "No blank in sentence",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "api_key": "test"
    })
    if res_bad.status_code != 400:
        print(f"[FAIL] Sentence validation expected 400, got {res_bad.status_code}")
        sys.exit(1)
    print("[OK] Blank sentence validation verified (400 returned).")

    res_nokey = client.post("/api/expand", json={
        "sentence_with_blank": "I steeped the leaves in _.",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "api_key": ""
    })
    if res_nokey.status_code != 400:
        print(f"[FAIL] BYOK key check expected 400, got {res_nokey.status_code}")
        sys.exit(1)
    print("[OK] In-memory BYOK check verified (400 returned).")

    print("\n=== 2. REAL SERVER HTTP SOCKET E2E TEST ===")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    proc = subprocess.Popen([sys.executable, "app.py"], cwd=root_dir)
    time.sleep(2)

    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/api/config")
        status = req.getcode()
        body = req.read().decode("utf-8")
        if status != 200:
            print(f"[FAIL] Live HTTP server returned status {status}")
            sys.exit(1)
        print("[OK] Live HTTP server response 200 OK:")
        print(body)
    finally:
        proc.terminate()
        proc.wait()

    print("\n=== E2E SKILL EVALUATION PASSED CLEANLY ===")

if __name__ == "__main__":
    main()
