from typing import Optional, Iterable
from anthropic import Anthropic
from app.core.llms.shared_prompt import build_prompt

# Default Claude model; can be overridden per request
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-sonnet-20240620"

# Optional allowlist to restrict usable models. Set to None to allow any.
ALLOWED_ANTHROPIC_MODELS: Optional[Iterable[str]] = {
    "claude-3-5-sonnet-20240620",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    # Add newer Anthropic models here as needed
}


def generate(access_counts: dict, api_key: str, model: Optional[str] = None) -> str:
    """
    Generate HOT/WARM/COLD classifications using Anthropic Claude.

    - Uses Anthropic official SDK (no OpenRouter).
    - Requires explicit api_key (no env fallback).
    - model: any Anthropic Claude model string; defaults to DEFAULT_ANTHROPIC_MODEL.
    - Returns raw text; llm_factory handles JSON cleaning/parsing.
    """
    if not access_counts:
        return "No access data provided."

    if not api_key:
        raise ValueError("Claude API error: API key is required but missing.")

    chosen_model = (model or DEFAULT_ANTHROPIC_MODEL).strip()
    if ALLOWED_ANTHROPIC_MODELS is not None and chosen_model not in ALLOWED_ANTHROPIC_MODELS:
        raise ValueError(f"Claude API error: Model '{chosen_model}' is not allowed.")

    prompt = build_prompt(access_counts)

    try:
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=chosen_model,
            max_tokens=2000,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )

        if not resp or not getattr(resp, "content", None):
            raise ValueError("Claude API returned an invalid response.")

        # Concatenate all text blocks from the response
        parts = []
        for block in resp.content:
            if getattr(block, "type", "") == "text" and hasattr(block, "text"):
                parts.append(block.text)

        text = "\n".join(parts).strip()
        if not text:
            raise ValueError("Claude API returned empty content.")

        return text

    except Exception as e:
        raise ValueError(f"Claude API error: {e}")
