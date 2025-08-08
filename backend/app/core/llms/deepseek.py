from typing import Optional, Iterable
import requests
from app.core.llms.shared_prompt import build_prompt

# Default DeepSeek model; can be overridden per request
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

# Optional allowlist. Set to None to allow any DeepSeek model string.
ALLOWED_DEEPSEEK_MODELS: Optional[Iterable[str]] = {
    "deepseek-chat",
    "deepseek-reasoner",
    # add more official DeepSeek models here as needed
}

API_BASE = "https://api.deepseek.com/v1/chat/completions"


def generate(access_counts: dict, api_key: str, model: Optional[str] = None) -> str:
    """
    Generate HOT/WARM/COLD classifications using DeepSeek models.

    - Uses DeepSeek official HTTP API (no OpenRouter).
    - Requires explicit api_key (no env fallback).
    - model: any DeepSeek model string; defaults to DEFAULT_DEEPSEEK_MODEL.
    - Returns raw text; llm_factory handles JSON cleaning/parsing.
    """
    if not access_counts:
        return "No access data provided."

    if not api_key:
        raise ValueError("DeepSeek API error: API key is required but missing.")

    chosen_model = (model or DEFAULT_DEEPSEEK_MODEL).strip()
    if ALLOWED_DEEPSEEK_MODELS is not None and chosen_model not in ALLOWED_DEEPSEEK_MODELS:
        raise ValueError(f"DeepSeek API error: Model '{chosen_model}' is not allowed.")

    prompt = build_prompt(access_counts)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": chosen_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 2000,
    }

    try:
        resp = requests.post(API_BASE, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Expect OpenAI-compatible shape
        if not data or "choices" not in data or not data["choices"]:
            raise ValueError("DeepSeek API returned an invalid response.")

        message = data["choices"][0].get("message", {})
        content = (message.get("content") or "").strip()
        if not content:
            raise ValueError("DeepSeek API returned empty content.")

        return content

    except requests.HTTPError as e:
        # Bubble up useful server error text if present
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise ValueError(f"DeepSeek API error (HTTP): {e}; details: {err}")
    except Exception as e:
        raise ValueError(f"DeepSeek API error: {e}")
