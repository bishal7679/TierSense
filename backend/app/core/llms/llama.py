import os
import json
import requests
import re

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-project-site.com",
        "X-Title": "TierSense"
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",  # ✅ Free model on OpenRouter
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]

        print("🔍 LLaMA LLM response:")
        print(repr(raw))

        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"LLaMA API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"LLaMA response parsing error: {parse_err}"
    except Exception as e:
        return f"LLaMA unexpected error: {e}"

def _build_prompt(access_counts: dict) -> str:
    prompt = (
        "You're a file tiering engine. Classify file paths into storage tiers:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Occasionally accessed\n"
        "- COLD: Rarely accessed\n\n"
        "Respond only in valid JSON format like:\n"
        "{\n  \"/mnt/file.txt\": \"HOT\",\n  \"/mnt/archive/file.txt\": \"COLD\"\n}\n\n"
        "Access data:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt

def _extract_json(raw: str) -> str:
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()
    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
