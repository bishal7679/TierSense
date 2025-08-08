from typing import Optional, Iterable
from openai import OpenAI
from app.core.llms.shared_prompt import build_prompt

# Default LLaMA model; override per request if needed
DEFAULT_LLAMA_MODEL = "meta-llama/llama-3.1-8b-instruct"

# Optional allowlist to prevent typos/unsupported names.
# Set to None to allow any model string your provider supports.
ALLOWED_LLAMA_MODELS: Optional[Iterable[str]] = {
    "meta-llama/llama-3.1-8b-instruct",
    "meta-llama/llama-3.1-70b-instruct",
    "meta-llama/llama-3-70b-instruct",
    "llama-3.1-8b-instruct",
    "llama-3.1-70b-instruct",
}

def _client(api_key: str, base_url: Optional[str] = None) -> OpenAI:
    """
    Create an OpenAI-compatible client.
    - api_key: provider API key (required).
    - base_url: provider base URL (e.g., "https://api.together.xyz/v1").
    """
    if not api_key:
        raise ValueError("LLaMA API error: API key is required but missing.")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)

def generate(
    access_counts: dict,
    api_key: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None
) -> str:
    """
    Generate HOT/WARM/COLD classifications with LLaMA models via an
    OpenAI-compatible Chat Completions API.

    Args:
        access_counts: dict[path -> count]
        api_key: provider API key (required)
        model: model name string supported by your provider
        base_url: provider base URL (e.g., Together/Groq OpenAI-compatible endpoint)

    Returns:
        Raw text content from the model (JSON string expected by upstream).
    """
    if not access_counts:
        return "No access data provided."

    chosen_model = (model or DEFAULT_LLAMA_MODEL).strip()
    if ALLOWED_LLAMA_MODELS is not None and chosen_model not in ALLOWED_LLAMA_MODELS:
        raise ValueError(f"LLaMA API error: Model '{chosen_model}' is not allowed.")

    prompt = build_prompt(access_counts)
    client = _client(api_key, base_url=base_url)

    try:
        resp = client.chat.completions.create(
            model=chosen_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,   # keep output deterministic for strict JSON
            max_tokens=2000
        )

        # Validate response structure
        if not resp or not getattr(resp, "choices", None):
            raise ValueError("LLaMA API returned an invalid response (no choices).")

        choice = resp.choices[0]
        msg = getattr(choice, "message", None)
        content = getattr(msg, "content", "").strip() if msg else ""

        if not content:
            raise ValueError("LLaMA API returned empty content.")

        return content

    except Exception as e:
        # Normalize error surface for callers
        raise ValueError(f"LLaMA API error: {e}")
