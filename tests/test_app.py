import pytest
import httpx
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app, clean_json_response, sanitize_replacement

client = TestClient(app)

# ---------------------------------------------------------------------------
# Unit Tests for Helper Functions
# ---------------------------------------------------------------------------

def test_clean_json_response_pure_json():
    raw = '{"replacement": "hot water for [[tea]]"}'
    res = clean_json_response(raw)
    assert res == {"replacement": "hot water for [[tea]]"}

def test_clean_json_response_markdown_enclosed():
    raw = '''```json
    {
      "replacement": "[[fresh brewed]] tea"
    }
    ```'''
    res = clean_json_response(raw)
    assert res == {"replacement": "[[fresh brewed]] tea"}

def test_clean_json_response_with_commentary():
    raw = 'Here is your response: {"replacement": "rich [[flavor]]"} hope you like it.'
    res = clean_json_response(raw)
    assert res == {"replacement": "rich [[flavor]]"}

def test_clean_json_response_invalid_json():
    with pytest.raises(ValueError, match="Could not parse valid JSON"):
        clean_json_response("This is not JSON at all.")

def test_sanitize_replacement_deduplication():
    # Consecutive phrase deduplication
    assert sanitize_replacement("fragrant jasmine-infused tea fragrant jasmine-infused tea") == "fragrant jasmine-infused tea"
    
    # Preceding word stripping
    sent = "I brew a cup of jasmine-infused _ ."
    res = sanitize_replacement("jasmine-infused [[fragrant]] tea", sentence_with_blank=sent)
    assert res == "[[fragrant]] tea"

    # Trailing word stripping
    sent2 = "I drank _ tea."
    res2 = sanitize_replacement("steeped herbal tea", sentence_with_blank=sent2)
    assert res2 == "steeped herbal"

    # Empty inputs
    assert sanitize_replacement("  ") == ""
    assert sanitize_replacement("hello world", sentence_with_blank="No blank here") == "hello world"


# ---------------------------------------------------------------------------
# Unit Tests for API Endpoints & Error Handling
# ---------------------------------------------------------------------------

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_get_config():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 1
    first_model = data["models"][0]
    assert "provider" in first_model
    assert "name" in first_model
    assert "id" in first_model


def test_expand_missing_blank():
    payload = {
        "sentence_with_blank": "No blank here",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "api_key": "test-key"
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 400
    assert "blank '_'" in response.json()["detail"]


def test_expand_missing_api_key():
    payload = {
        "sentence_with_blank": "I drank _ tea.",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "api_key": "   "
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 400
    assert "API Key is required" in response.json()["detail"]


def test_expand_unsupported_provider():
    payload = {
        "sentence_with_blank": "I drank _ tea.",
        "provider": "unknown_llm",
        "model": "some-model",
        "api_key": "test-key"
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 400
    assert "Unsupported provider" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Unit Tests for LLM Providers & Error Edge Cases (Mocked via httpx.Client)
# ---------------------------------------------------------------------------

def test_expand_anthropic_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": '{"replacement": "steeped [[hot water]]"}'}]
    }

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "api.anthropic.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "api_key": "valid-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 200
        assert response.json() == {"replacement": "steeped [[hot water]]"}


def test_expand_openai_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"replacement": "delicious [[oolong]]"}'}}]
    }

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "api.openai.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "api_key": "valid-openai-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 200
        assert response.json() == {"replacement": "delicious [[oolong]]"}


def test_expand_google_gemini_success():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"replacement": "warm [[chamomile]]"}'}]}}]
    }

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "generativelanguage.googleapis.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "google",
            "model": "gemini-3.5-flash",
            "api_key": "valid-gemini-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 200
        assert response.json() == {"replacement": "warm [[chamomile]]"}


def test_expand_anthropic_error_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Invalid API Key"

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "api.anthropic.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "anthropic",
            "model": "claude-haiku-4-5-20251001",
            "api_key": "invalid-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 401
        assert "Anthropic API error" in response.json()["detail"]


def test_expand_openai_error_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = "Rate limit exceeded"

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "api.openai.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "api_key": "invalid-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 429
        assert "OpenAI API error" in response.json()["detail"]


def test_expand_google_gemini_error_status():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "API key not valid"

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "generativelanguage.googleapis.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "google",
            "model": "gemini-3.5-flash",
            "api_key": "invalid-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 400
        assert "Gemini API error" in response.json()["detail"]


def test_expand_llm_empty_replacement():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"replacement": ""}'}}]
    }

    orig_post = httpx.Client.post

    def custom_post(self, url, *args, **kwargs):
        if "api.openai.com" in str(url):
            return mock_resp
        return orig_post(self, url, *args, **kwargs)

    with patch.object(httpx.Client, "post", new=custom_post):
        payload = {
            "sentence_with_blank": "I drank _ tea.",
            "provider": "openai",
            "model": "gpt-5.4-nano",
            "api_key": "valid-key"
        }
        response = client.post("/api/expand", json=payload)
        assert response.status_code == 500
        assert "AI expansion failed" in response.json()["detail"]
