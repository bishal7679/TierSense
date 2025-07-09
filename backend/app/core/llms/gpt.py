import os
import json
import requests
import re
from app.core.llms.shared_prompt import build_prompt  # Shared strict prompt

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
        "model": "mistralai/mistral-7b-instruct:free",  # or openai/gpt-3.5-turbo etc.
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if not data.get("choices") or "message" not in data["choices"][0]:
            raise ValueError("Empty or malformed LLM response")

        raw = data["choices"][0]["message"]["content"].strip()

        # Save raw output for inspection
        log_path = "logs/llm_raw_output.log"
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w") as f:
                f.write(raw)
        except Exception as log_err:
            print(f"Failed to write raw output: {log_err}")

        return _extract_json(raw)

    except Exception as e:
        return f"LLM error: {e}"


def _extract_json(raw: str) -> str:
    """
    Cleans and parses JSON from LLM response that might include markdown fences or extra text.
    """
    # Strip common markdown formatting
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    # Attempt to find only JSON-like structure in case of extra wrapping
    json_start = cleaned.find('{')
    json_end = cleaned.rfind('}')
    if json_start != -1 and json_end != -1:
        cleaned = cleaned[json_start:json_end+1]

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")