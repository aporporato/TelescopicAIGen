import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app import app, clean_json_response

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


# ---------------------------------------------------------------------------
# Unit Tests for API Endpoints
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
# Unit Tests for LLM Providers (Mocked)
# ---------------------------------------------------------------------------

@patch("httpx.post")
def test_expand_anthropic_success(mock_httpx_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "content": [{"text": '{"replacement": "steeped [[hot water]]"}'}]
    }
    mock_httpx_post.return_value = mock_resp

    payload = {
        "sentence_with_blank": "I drank _ tea.",
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "api_key": "valid-key"
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 200
    assert response.json() == {"replacement": "steeped [[hot water]]"}


@patch("app.OpenAI")
def test_expand_openai_success(mock_openai_cls):
    mock_client = MagicMock()
    mock_openai_cls.return_value = mock_client
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content='{"replacement": "delicious [[oolong]]"}'))
    ]
    mock_client.chat.completions.create.return_value = mock_completion

    payload = {
        "sentence_with_blank": "I drank _ tea.",
        "provider": "openai",
        "model": "gpt-5.4-nano",
        "api_key": "valid-openai-key"
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 200
    assert response.json() == {"replacement": "delicious [[oolong]]"}


@patch("app.genai.Client")
def test_expand_google_gemini_success(mock_genai_cls):
    mock_client = MagicMock()
    mock_genai_cls.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.text = '{"replacement": "warm [[chamomile]]"}'
    mock_client.models.generate_content.return_value = mock_resp

    payload = {
        "sentence_with_blank": "I drank _ tea.",
        "provider": "google",
        "model": "gemini-3.5-flash",
        "api_key": "valid-gemini-key"
    }
    response = client.post("/api/expand", json=payload)
    assert response.status_code == 200
    assert response.json() == {"replacement": "warm [[chamomile]]"}
