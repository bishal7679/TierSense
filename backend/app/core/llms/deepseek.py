import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-project-site.com",  # Optional but recommended
        "X-Title": "TierSense"
    }

    payload = {
        "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",  # ✅ FREE DeepSeek model
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        return _extract_json(raw)
    except Exception as e:
        return f"LLM API error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "You're an intelligent storage advisor.\n"
        "Classify file paths into these tiers based on access frequency:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Occasionally accessed\n"
        "- COLD: Rarely accessed\n"
        "Output should be strictly in this JSON format:\n"
        "{\n"
        "  \"/mnt/data/file1.txt\": \"HOT\",\n"
        "  \"/mnt/data/old.zip\": \"COLD\"\n"
        "}\n\n"
        "Access statistics:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt

def _extract_json(raw: str) -> str:
    try:
        if raw.strip().startswith("```"):
            raw = raw.strip().strip("```json").strip("```").strip()
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
