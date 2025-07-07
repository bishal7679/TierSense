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
import re
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response["choices"][0]["message"]["content"]
        print("🔍 Raw GPT Response:\n", raw)  # Debug log

        cleaned = _extract_json(raw)
        return json.dumps(cleaned, indent=2)  # Always return valid JSON string

    except Exception as e:
        return f"OpenAI GPT error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "You are a system that classifies file paths based on access frequency.\n"
        "Classify each path into one of the following tiers:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Moderately accessed\n"
        "- COLD: Rarely accessed\n\n"
        "Respond ONLY in raw JSON format like this:\n"
        "{\n  \"/mnt/data/file1\": \"HOT\",\n  \"/mnt/data/file2\": \"COLD\"\n}\n"
        "Do NOT include any explanations, markdown, or extra text.\n\n"
        "Here is the data:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt

def _extract_json(raw: str) -> dict:
    if not raw or raw.strip() == "":
        raise ValueError("Empty response received from GPT")

    # Remove markdown-style triple backtick blocks
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE | re.IGNORECASE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nRaw content:\n{cleaned}")
