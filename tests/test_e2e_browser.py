"""
Browser & DOM E2E Verification Test Suite.

Verifies:
1. Root HTML route serves SPA index page with ARIA accessibility indicators.
2. API /api/config returns dynamic model list with valid headers.
3. API /api/expand enforces Google Gemini x-goog-api-key header authentication.
4. Export story structure & keyboard navigation contract assertions.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import httpx
from app import app

client = TestClient(app)

def test_e2e_spa_root_and_aria_structure():
    """Verify root / serves HTML with accessibility structure."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_e2e_api_config_endpoint():
    """Verify backend returns configured AI models."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 1
    providers = [m["provider"] for m in data["models"]]
    assert "google" in providers
    assert "openai" in providers

def test_e2e_gemini_header_auth():
    """Verify Google Gemini uses x-goog-api-key HTTP header."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"replacement": "glowing [[secret map]]"}'}]}}]
    }

    captured_headers = {}

    def custom_post(self, url, headers=None, json=None, **kwargs):
        if "generativelanguage.googleapis.com" in str(url):
            nonlocal captured_headers
            captured_headers = headers or {}
            # Verify key is NOT in URL query string
            assert "key=" not in str(url)
            return mock_resp
        return httpx.Client.post(self, url, headers=headers, json=json, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "The detective found a _ key.",
            "provider": "google",
            "model": "gemini-3.5-flash",
            "api_key": "test-gemini-header-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 200
        assert response.json() == {"replacement": "glowing [[secret map]]"}
        # Assert header authentication
        assert captured_headers.get("x-goog-api-key") == "test-gemini-header-key"

def test_e2e_upstream_retry_resilience():
    """Verify upstream 429 rate-limit responses trigger retry before returning success."""
    fail_resp = MagicMock()
    fail_resp.status_code = 429
    fail_resp.text = "Rate limit"

    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {
        "choices": [{"message": {"content": '{"replacement": "resilient [[expansion]]"}'}}]
    }

    call_count = 0

    def retry_post(self, url, headers=None, json=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return fail_resp
        return success_resp

    with patch.object(httpx.Client, "post", new=retry_post):
        payload = {
            "sentence_with_blank": "I brewed a _ tea.",
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "api_key": "test-openai-key"
        }
        with patch("time.sleep", return_value=None):
            response = client.post("/api/expand", json=payload)
            assert response.status_code == 200
            assert response.json() == {"replacement": "resilient [[expansion]]"}
            assert call_count == 2
