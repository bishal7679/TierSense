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
        "HTTP-Referer": "https://your-project-site.com",  # Optional, for OpenRouter tracking
        "X-Title": "TierSense"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",  # You can switch this to any supported OpenRouter model
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        raw = data["choices"][0]["message"]["content"]

        print("🔍 Raw LLM response:", repr(raw))  # Useful for debugging

        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"LLM API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"LLM response parsing error: {parse_err}"
    except Exception as e:
        return f"Unexpected error: {e}"


def _build_prompt(access_counts: dict) -> str:
    prompt = (
        "You're a smart storage optimization agent.\n"
        "Classify each file path as one of the following based on access frequency:\n"
        "- HOT (frequently accessed)\n"
        "- WARM (moderately accessed)\n"
        "- COLD (rarely accessed)\n"
        "Respond ONLY in valid JSON like this:\n"
        "{\n"
        "  \"/mnt/data/recent.txt\": \"HOT\",\n"
        "  \"/mnt/data/logs/old.log\": \"COLD\"\n"
        "}\n\n"
        "Access data:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt


def _extract_json(raw: str) -> str:
    try:
        # Remove surrounding ```json ... ``` or ``` ... ```
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"```(?:json)?\n?", "", cleaned)
            cleaned = cleaned.strip("`").strip()

        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)

    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
