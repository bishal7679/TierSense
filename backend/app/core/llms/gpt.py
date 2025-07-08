import os
import json
import requests
import re
from app.core.llms.shared_prompt import build_prompt  # Import shared logic

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = build_prompt(access_counts)  # Use shared prompt

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "TierSense"
    }

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)

        if response.status_code != 200:
            return f"OpenRouter API error: {response.status_code} - {response.text}"

        data = response.json()
        raw = data["choices"][0]["message"]["content"]

        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"LLM API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"LLM response parsing error: {parse_err}"
    except Exception as e:
        return f"Unexpected error: {e}"


def _extract_json(raw: str) -> str:
    try:
        with open("/home/ubuntu/llm_raw_output.log", "w") as f:
            f.write(raw)
    except Exception as e:
        print(f"Failed to write raw output: {e}")

    # Strip markdown/code block wrappers
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")