import os
import json
import requests
import re
from app.core.llms.shared_prompt import build_prompt  # Central rule-based logic

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
        "model": "meta-llama/llama-3.1-8b-instruct", 
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if "choices" not in data or not data["choices"]:
            return f"OpenRouter returned invalid structure: {data}"

        raw = data["choices"][0]["message"]["content"]
        print("LLaMA raw response (first 100 chars):", repr(raw[:100]))

        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"LLaMA API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"LLaMA response parsing error: {parse_err}"
    except Exception as e:
        return f"LLaMA unexpected error: {e}"


def _extract_json(raw: str) -> str:
    # Save raw LLM output for debugging
    try:
        log_path = "logs/llm_raw_output.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w") as f:
            f.write(raw)
    except Exception as log_err:
        print(f"⚠️ Failed to write raw output to log: {log_err}")

    # Strip triple-backtick markdown code block
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")