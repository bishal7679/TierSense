from typing import Optional, Iterable
from openai import OpenAI
from app.core.llms.shared_prompt import build_prompt

# Default OpenAI model; can be overridden per request
DEFAULT_GPT_MODEL = "gpt-4o-mini"

# Optional allowlist. Set to None to allow any OpenAI model string.
ALLOWED_OPENAI_MODELS: Optional[Iterable[str]] = {
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4.1",
    "gpt-4.1-mini",
    "o4-mini",
    "o4",
    # add more as needed
}

def _client(api_key: str) -> OpenAI:
    if not api_key:
        raise ValueError("GPT API error: API key is required but missing.")
    return OpenAI(api_key=api_key)

def generate(access_counts: dict, api_key: str, model: Optional[str] = None) -> str:
    """
    Generate HOT/WARM/COLD classifications with any OpenAI GPT-family model.

    - Uses OpenAI official SDK (no OpenRouter).
    - Requires explicit api_key (no env fallback).
    - model: any OpenAI model string; defaults to DEFAULT_GPT_MODEL.
    - Returns raw text; llm_factory handles JSON cleaning/parsing.
    """
    if not access_counts:
        return "No access data provided."

    chosen_model = (model or DEFAULT_GPT_MODEL).strip()

    # Optional safeguard: enforce allowlist to avoid typos/unsupported names
    if ALLOWED_OPENAI_MODELS is not None and chosen_model not in ALLOWED_OPENAI_MODELS:
        raise ValueError(f"GPT API error: Model '{chosen_model}' is not allowed.")

    client = _client(api_key)
    prompt = build_prompt(access_counts)

    try:
        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,   # keep JSON consistent
            max_tokens=2000
        )

        if not resp or not resp.choices or not resp.choices[0].message or not resp.choices[0].message.content:
            raise ValueError("GPT API returned an invalid response.")

        return resp.choices[0].message.content.strip()

    except Exception as e:
        raise ValueError(f"GPT API error: {e}")
