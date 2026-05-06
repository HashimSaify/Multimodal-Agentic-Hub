import os
import base64
import requests
from functools import lru_cache
from typing import Optional

def _call_custom_api(prompt: str) -> str:
    api_key = os.getenv("IMAGE_API_KEY")
    model_name = os.getenv("IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    base_url = os.getenv("IMAGE_BASE_URL", "https://api-inference.huggingface.co/models/")

    if not api_key:
        raise RuntimeError("IMAGE_API_KEY is not set in .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Hugging Face Inference API URL format
    url = f"{base_url.rstrip('/')}/{model_name}"
    
    payload = {
        "inputs": prompt,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        
        # Check if the model is still loading (common in HF Inference API)
        if response.status_code == 503:
            # You might want to retry or handle this, but for now we'll just report it
            raise RuntimeError("Hugging Face model is still loading. Please try again in a few seconds.")
            
        response.raise_for_status()
        
        # Hugging Face returns raw bytes for images
        return base64.b64encode(response.content).decode("utf-8")
        
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                if "error" in error_data:
                    err_msg = error_data["error"]
            except:
                err_msg += f" - Response: {e.response.text}"
        raise RuntimeError(f"Image API error: {err_msg}")


@lru_cache(maxsize=64)
def _cached_generate_images(topic: str, grade_level: str):
    diagram_prompt = (
        f"Create a high quality, clean educational diagram about {topic}. "
        "Show the visual concepts clearly. DO NOT include any text, labels, words, or letters in the image. "
        "The image should be entirely text-free, relying only on visuals and shapes. White background."
    )

    diagram_b64 = _call_custom_api(diagram_prompt)

    return {
        "diagram_b64": diagram_b64,
        "flashcard_b64": None,
    }


def generate_images(topic: str, grade_level: Optional[str]):
    return _cached_generate_images(topic, grade_level or "")

