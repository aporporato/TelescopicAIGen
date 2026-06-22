# app.py
import os
import json
import logging
import re
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
            {"provider": "openai", "name": "OpenAI gpt-5.4-nano", "id": "gpt-5.4-nano"},
            {"provider": "google", "name": "Google gemini-3.5-flash", "id": "gemini-3.5-flash"},
            {"provider": "anthropic", "name": "Anthropic claude-haiku-4-5", "id": "claude-haiku-4-5-20251001"}
        ]
else:
    available_models = [
        {"provider": "openai", "name": "OpenAI gpt-5.4-nano", "id": "gpt-5.4-nano"},
        {"provider": "google", "name": "Google gemini-3.5-flash", "id": "gemini-3.5-flash"},
        {"provider": "anthropic", "name": "Anthropic claude-haiku-4-5", "id": "claude-haiku-4-5-20251001"}
    ]

# Mount static and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

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
    
    system_prompt = """You are a backend JSON API for a Telescopic Text writing application.
Your ONLY task is to expand a blank "_" in a sentence and return a JSON object containing the replacement phrase.

CRITICAL INSTRUCTIONS:
1. You must respond ONLY with a raw JSON object.
2. Do NOT write any conversational introduction, markdown blocks, warnings, code enclosures, self-corrections, or trailing comments.
3. Your output must start with '{' and end with '}'.
4. The output JSON must have exactly one key: "replacement".

JSON Schema:
{
  "replacement": "the replacement phrase with 1 to 2 words wrapped in [[brackets]]"
}"""

    user_prompt = f"""Expand the blank "_" in the following sentence with a detailed, creative phrase of 2 to 6 words.
Wrap 1 to 2 words inside your expansion in [[brackets]] to make them expandable triggers for the reader. Do not wrap everything.

Sentence: "{sentence}"
"""

    try:
        import httpx
        
        if provider == "anthropic":
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            json_data = {
                "model": model,
                "max_tokens": 100,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}]
            }
            response = httpx.post(url, headers=headers, json=json_data, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Anthropic API error: {response.text}")
            raw_text = response.json()["content"][0]["text"]
            
        elif provider == "openai":
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
                "max_tokens": 100,
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            response = httpx.post(url, headers=headers, json=json_data, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"OpenAI API error: {response.text}")
            raw_text = response.json()["choices"][0]["message"]["content"]
            
        elif provider == "google":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            headers = {
                "content-type": "application/json"
            }
            json_data = {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [{
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "maxOutputTokens": 100,
                    "temperature": 0.7
                }
            }
            response = httpx.post(url, headers=headers, json=json_data, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {response.text}")
            raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
            
        logger.info(f"Raw response from {provider} ({model}): {raw_text}")
        
        parsed_response = clean_json_response(raw_text)
        replacement = parsed_response.get("replacement", "").strip()
        
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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
