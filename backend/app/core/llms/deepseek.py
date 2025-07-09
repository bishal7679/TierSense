import os
import json
import requests
import re
from app.core.llms.shared_prompt import build_prompt

# OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate(access_counts: dict, api_key: str = None) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = build_prompt(access_counts)

    # Fallback to env if no key passed
    final_key = api_key or os.getenv("OPENROUTER_API_KEY")

    if not final_key:
        return "No API key provided."

    headers = {
        "Authorization": f"Bearer {final_key}",
        "Content-Type": "application/json",
        "X-Title": "TierSense"
    }

    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]

        print("📦 DeepSeek LLM response:")
        print(repr(raw))  # for debugging

        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"DeepSeek API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"DeepSeek response parsing error: {parse_err}"
    except Exception as e:
        return f"DeepSeek unexpected error: {e}"


def _extract_json(raw: str) -> str:
    # output if wrapped in ```json ... ```
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")