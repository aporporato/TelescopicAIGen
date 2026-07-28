# app.py
import os
import json
import logging
import re
import time
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Telescopic Text")

# Load available models configuration from .env or use defaults
available_models_json = os.getenv("AVAILABLE_MODELS")
if available_models_json:
    try:
        available_models = json.loads(available_models_json)
    except Exception as e:
        logger.error(f"Error parsing AVAILABLE_MODELS JSON: {e}")
        available_models = [
            {"provider": "openai", "name": "GPT-5.4 Nano", "id": "gpt-5.4-nano"},
            {"provider": "google", "name": "Gemini 3.5 Flash", "id": "gemini-3.5-flash"},
            {"provider": "anthropic", "name": "Claude Haiku 4.5", "id": "claude-haiku-4-5-20251001"}
        ]
else:
    available_models = [
        {"provider": "openai", "name": "GPT-5.4 Nano", "id": "gpt-5.4-nano"},
        {"provider": "google", "name": "Gemini 3.5 Flash", "id": "gemini-3.5-flash"},
        {"provider": "anthropic", "name": "Claude Haiku 4.5", "id": "claude-haiku-4-5-20251001"}
    ]

class ExpandRequest(BaseModel):
    sentence_with_blank: str
    provider: str
    model: str
    api_key: str

def clean_json_response(text: str) -> dict:
    text = text.strip()
    
    # Attempt to locate and parse any isolated JSON block
    matches = re.findall(r'\{.*?\}', text, re.DOTALL)
    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue
            
    # Fallback to absolute bounds
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError:
            pass
            
    raise ValueError(f"Could not parse valid JSON from LLM response: {text}")

def sanitize_replacement(replacement: str, sentence_with_blank: str = "") -> str:
    replacement = replacement.strip()
    
    # 1. Remove accidental duplicated consecutive phrases (e.g. "X Y X Y" -> "X Y")
    tokens = replacement.split()
    if len(tokens) >= 4 and len(tokens) % 2 == 0:
        half = len(tokens) // 2
        if tokens[:half] == tokens[half:]:
            replacement = " ".join(tokens[:half])
            tokens = replacement.split()

    # 2. Strip duplicate preceding/trailing words if LLM repeats words immediately surrounding the blank
    if sentence_with_blank and "_" in sentence_with_blank:
        parts = sentence_with_blank.split("_")
        before_text = parts[0].strip()
        after_text = parts[1].strip() if len(parts) > 1 else ""
        
        before_words = [re.sub(r'^\W+|\W+$', '', w).lower() for w in before_text.split() if w.strip()]
        after_words = [re.sub(r'^\W+|\W+$', '', w).lower() for w in after_text.split() if w.strip()]

        # Check if replacement starts with the last word before blank (e.g. "jasmine-infused")
        if before_words and tokens:
            last_before = before_words[-1]
            first_rep_clean = re.sub(r'[\[\]]', '', re.sub(r'^\W+|\W+$', '', tokens[0])).lower()
            if first_rep_clean and first_rep_clean == last_before:
                tokens.pop(0)

        # Check if replacement ends with the first word after blank
        if after_words and tokens:
            first_after = after_words[0]
            last_rep_clean = re.sub(r'[\[\]]', '', re.sub(r'^\W+|\W+$', '', tokens[-1])).lower()
            if last_rep_clean and last_rep_clean == first_after:
                tokens.pop(-1)

        replacement = " ".join(tokens)

    return replacement

def post_with_retry(client: httpx.Client, url: str, headers: dict, json_data: dict, max_retries: int = 2) -> httpx.Response:
    for attempt in range(max_retries + 1):
        resp = client.post(url, headers=headers, json=json_data)
        if resp.status_code in (429, 503) and attempt < max_retries:
            logger.warning(f"Upstream status {resp.status_code}, retrying attempt {attempt + 1}/{max_retries}...")
            time.sleep(1.0)
            continue
        return resp
    return resp

# ---------------------------------------------------------------------------
# API Endpoints (Declared before static files mount)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pluggable LLM Provider Strategy Registry
# ---------------------------------------------------------------------------

class LLMProviderAdapter:
    def format_request(self, model: str, api_key: str, system_prompt: str, user_prompt: str) -> tuple[str, dict, dict]:
        raise NotImplementedError

    def parse_response(self, response: httpx.Response) -> str:
        raise NotImplementedError

class AnthropicAdapter(LLMProviderAdapter):
    def format_request(self, model: str, api_key: str, system_prompt: str, user_prompt: str):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        json_data = {
            "model": model,
            "max_tokens": 1000,
            "temperature": 0.7,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        return url, headers, json_data

    def parse_response(self, response: httpx.Response) -> str:
        return response.json()["content"][0]["text"]

class OpenAIAdapter(LLMProviderAdapter):
    def format_request(self, model: str, api_key: str, system_prompt: str, user_prompt: str):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json"
        }
        json_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7,
            "response_format": {"type": "json_object"}
        }
        return url, headers, json_data

    def parse_response(self, response: httpx.Response) -> str:
        return response.json()["choices"][0]["message"]["content"]

class GoogleGeminiAdapter(LLMProviderAdapter):
    def format_request(self, model: str, api_key: str, system_prompt: str, user_prompt: str):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        headers = {
            "content-type": "application/json",
            "x-goog-api-key": api_key
        }
        json_data = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": 1000,
                "temperature": 0.7
            }
        }
        return url, headers, json_data

    def parse_response(self, response: httpx.Response) -> str:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]

# Pluggable Provider Registry - To add a new provider (e.g. Mistral, Groq, DeepSeek), add adapter here.
PROVIDER_REGISTRY: dict[str, LLMProviderAdapter] = {
    "anthropic": AnthropicAdapter(),
    "openai": OpenAIAdapter(),
    "google": GoogleGeminiAdapter(),
}

@app.get("/api/config")
def get_config():
    return {"models": available_models}

@app.post("/api/expand")
def expand_sentence(payload: ExpandRequest):
    sentence = payload.sentence_with_blank.strip()
    if "_" not in sentence:
        raise HTTPException(status_code=400, detail="Sentence must contain a blank '_' character.")
    
    provider = payload.provider.strip().lower()
    model = payload.model.strip()
    api_key = payload.api_key.strip()
            
    if not api_key:
        raise HTTPException(status_code=400, detail=f"An API Key is required to run the {provider.title()} model.")

    adapter = PROVIDER_REGISTRY.get(provider)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
    
    system_prompt = """You are a backend JSON API for a Telescopic Text writing application.
Your ONLY task is to expand a blank "_" in a sentence and return a JSON object containing the replacement phrase.

<instructions level=critical">
1. You must respond ONLY with a raw JSON object.
2. Do NOT write any conversational introduction, markdown blocks, warnings, code enclosures, self-corrections, or trailing comments.
3. Your output must start with '{' and end with '}'.
4. The output JSON must have exactly one key: "replacement".
5. The replacement phrase replaces ONLY the blank "_". Do NOT repeat words that appear immediately BEFORE or AFTER the blank in the sentence.
6. Do NOT repeat the target word being expanded at the end of your replacement.

JSON Schema:
{
  "replacement": "the replacement phrase with 1 to 2 words wrapped in [[brackets]]"
}

</instructions>

<example>
Input sentence: "The detective found a _ key."
Output: {"replacement": "mysterious [[glowing]]"}
</example>"""

    user_prompt = f"""Expand the blank "_" in the following sentence with a single, creative, non-redundant phrase of 2 to 6 words.
Wrap 1 to 2 words inside your expansion in [[brackets]] to make them expandable triggers for the reader. Do not wrap everything.
Do NOT repeat the word being expanded or any words that appear immediately before or after the blank.

Sentence: "{sentence}"
"""

    try:
        url, headers, json_data = adapter.format_request(model, api_key, system_prompt, user_prompt)
        with httpx.Client(verify=False, timeout=30.0) as http_client:
            response = post_with_retry(http_client, url, headers, json_data)
            if response.status_code != 200:
                prefixes = {"openai": "OpenAI", "google": "Gemini", "anthropic": "Anthropic"}
                prefix = prefixes.get(provider, provider.title())
                raise HTTPException(status_code=response.status_code, detail=f"{prefix} API error: {response.text}")
            raw_text = adapter.parse_response(response)
                
        logger.info(f"Raw response from {provider} ({model}): {raw_text}")
        
        parsed_response = clean_json_response(raw_text)
        replacement = parsed_response.get("replacement", "").strip()
        replacement = sanitize_replacement(replacement, sentence_with_blank=sentence)
        
        if not replacement:
            raise ValueError("Empty 'replacement' key in LLM response")
            
        return {
            "replacement": replacement
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise HTTPException(status_code=500, detail=f"AI expansion failed: {str(e)}")

# ---------------------------------------------------------------------------
# Angular SPA Static Files Mount
# ---------------------------------------------------------------------------

dist_dir = "dist"
if os.path.exists(os.path.join(dist_dir, "browser")):
    dist_dir = os.path.join(dist_dir, "browser")

if os.path.exists(dist_dir):
    app.mount("/", StaticFiles(directory=dist_dir, html=True), name="angular_spa")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
