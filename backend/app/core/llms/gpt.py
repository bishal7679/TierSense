# import os
# import openai

# openai.api_key = os.getenv("OPENAI_API_KEY")

# def generate(access_counts: dict) -> str:
#     if not access_counts:
#         return "No access data provided."

#     prompt = _build_prompt(access_counts)
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response["choices"][0]["message"]["content"].strip()
#     except Exception as e:
#         return f"OpenAI GPT error: {e}"

# def _build_prompt(access_counts):
#     prompt = (
#         "You're a storage optimization system.\n"
#         "Classify paths as HOT/WARM/COLD based on access frequency.\n"
#         "Return valid JSON.\n\n"
#     )
#     for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
#         prompt += f"{path}: {count}\n"
#     return prompt

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
        "HTTP-Referer": "https://your-project-site.com",  # Optional, but good practice
        "X-Title": "TierSense"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",  # or another model like "mistralai/mixtral-8x7b"
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw = data["choices"][0]["message"]["content"]
        print("🔍 Raw LLM response:", repr(raw))
        return _extract_json(raw)
    except Exception as e:
        return f"LLM API error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "Classify file paths into storage tiers based on access frequency:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Occasionally accessed\n"
        "- COLD: Rarely accessed\n"
        "Respond in pure JSON format only. Example:\n"
        "{\n  \"/mnt/file.txt\": \"HOT\",\n  \"/mnt/oldfile.txt\": \"COLD\"\n}\n\n"
        "Here is the input:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt

def _extract_json(raw: str) -> str:
    try:
        # Clean markdown
        if raw.strip().startswith("```"):
            raw = raw.strip().strip("```json").strip("```").strip()
        parsed = json.loads(raw)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
