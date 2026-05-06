import os
import json
import requests
from functools import lru_cache
from typing import Optional

from .schemas import GenerateContentResponse
from utils.prompts import build_prompt, build_validation_prompt


def _safe_json(text: str) -> dict:
    if not text:
        return {
            "overview": "",
            "key_points": [],
            "real_world_example": "",
            "flashcards": [],
            "summary": "",
        }
    cleaned = text.strip()
    if "{" in cleaned:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            cleaned = cleaned[start:end+1]
        
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned.replace("json", "", 1).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "flashcards" in data and isinstance(data["flashcards"], list):
            new_fc = []
            for item in data["flashcards"]:
                if isinstance(item, dict):
                    q = item.get("front") or item.get("question") or item.get("term") or item.get("q")
                    a = item.get("back") or item.get("answer") or item.get("definition") or item.get("a")
                    
                    if not q and not a:
                        # If both are missing, use the whole item as back
                        q = "Question"
                        a = str(item)
                    elif not q:
                        q = "Question"
                    elif not a:
                        a = "See front"
                        
                    # Strip redundant labels
                    q = q.replace("Front:", "").replace("front:", "").replace("Question:", "").strip()
                    a = a.replace("Back:", "").replace("back:", "").replace("Answer:", "").strip()
                    new_fc.append({"front": q, "back": a})
                elif isinstance(item, str):
                    # Handle cases where model returns a single string with labels
                    import re
                    # Look for Front: and Back: potentially wrapped in asterisks
                    f_pattern = r'(?:\*\*|)?Front:(?:\*\*|)?\s*(.*?)\s*(?:\*\*|)?Back:(?:\*\*|)?'
                    b_pattern = r'(?:\*\*|)?Back:(?:\*\*|)?\s*(.*)'
                    
                    f_match = re.search(f_pattern, item, re.IGNORECASE | re.DOTALL)
                    b_match = re.search(b_pattern, item, re.IGNORECASE | re.DOTALL)
                    
                    if f_match and b_match:
                        new_fc.append({"front": f_match.group(1).strip(), "back": b_match.group(2).strip()})
                    elif "|||" in item:
                        parts = item.split("|||", 1)
                        new_fc.append({"front": parts[0].strip(), "back": parts[1].strip()})
                    elif " - " in item:
                        parts = item.split(" - ", 1)
                        new_fc.append({"front": parts[0].strip(), "back": parts[1].strip()})
                    elif ":" in item:
                        parts = item.split(":", 1)
                        new_fc.append({"front": parts[0].strip(), "back": parts[1].strip()})
                    else:
                        new_fc.append({"front": "Key Concept", "back": item.strip()})
            data["flashcards"] = new_fc
        return data
    except json.JSONDecodeError:
        return {
            "overview": cleaned,
            "key_points": [],
            "real_world_example": "",
            "flashcards": [],
            "summary": "",
        }


@lru_cache(maxsize=128)
def _cached_generate_content(topic: str, grade_level: str):
    api_key = os.getenv("LLM_API_KEY")
    model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    # Native endpoint uses models/{model}:generateContent
    base_url = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")

    if not api_key:
        raise RuntimeError("LLM_API_KEY is not set in environment")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://multimodal-agentic-hub.local", # Required by OpenRouter
        "X-Title": "Multimodal Agentic Hub" # Required by OpenRouter
    }
    
    url = base_url

    # OpenAI-compatible payload (works with OpenRouter)
    val_payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": build_validation_prompt(topic)}],
        "temperature": 0.1,
        "max_tokens": 10
    }
    try:
        val_res = requests.post(url, headers=headers, json=val_payload, timeout=30)
        if val_res.status_code == 200:
            val_text = val_res.json()["choices"][0]["message"]["content"].strip().upper()
            if "NO" in val_text and "YES" not in val_text:
                return {
                    "error": "This topic does not appear to be related to education. Please ask about an academic subject, concept, or formal skill."
                }
            if "NO" in val_text and "YES" in val_text:
                if val_text.startswith("NO"):
                    return {
                        "error": "This topic does not appear to be related to education. Please ask about an academic subject, concept, or formal skill."
                    }
    except Exception:
        pass

    # Step 2: Generate Content
    prompt = build_prompt(topic, grade_level or None)
    
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 2048
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        text_out = response.json()["choices"][0]["message"]["content"]
        return _safe_json(text_out)
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            err_msg += f" - Response: {e.response.text}"
        raise RuntimeError(f"LLM API request failed: {err_msg}")


def generate_content(topic: str, grade_level: Optional[str]) -> GenerateContentResponse:
    data = _cached_generate_content(topic, grade_level or "")
    return GenerateContentResponse(**data)
