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
import re

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-project-site.com",  # Optional
        "X-Title": "TierSense"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",  # ✅ You can also test: "mistralai/mistral-7b-instruct:free"
        "messages": [
            {"role": "user", "content": prompt}
        ]
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


def _build_prompt(access_counts: dict) -> str:
    prompt = (
        "You are a file access tiering assistant.\n"
        "Classify each file path into one of the tiers: HOT (frequently accessed), WARM (moderately accessed), or COLD (rarely accessed).\n"
        "Return ONLY a valid JSON object without any explanation, markdown, or formatting.\n"
        "Example:\n"
        "{\n  \"/mnt/data/file1.txt\": \"HOT\",\n  \"/mnt/data/oldfile.txt\": \"COLD\"\n}\n\n"
        "Input:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt


def _extract_json(raw: str) -> str:
    # ✅ Write raw output to file for inspection
    with open("/tmp/llm_raw_output.log", "w") as f:
        f.write(raw)

    # ✅ Remove ```json ... ``` if exists
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
