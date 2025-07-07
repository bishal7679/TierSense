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
import openai
import json
import re

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
        raw = response["choices"][0]["message"]["content"].strip()
        print("GPT RAW:", raw)  # For debugging

        # Try extracting valid JSON from markdown or text
        cleaned = _extract_json(raw)

        return json.dumps(cleaned, indent=2)  # Return as stringified JSON

    except Exception as e:
        return f"OpenAI GPT error: {e}"


def _build_prompt(access_counts):
    prompt = (
        "You are a system that classifies file paths into storage tiers based on access frequency.\n"
        "Tiers:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Moderately accessed\n"
        "- COLD: Rarely accessed\n\n"
        "Respond ONLY in this JSON format:\n"
        "{\n  \"/path/to/file1\": \"HOT\",\n  \"/path/to/file2\": \"COLD\"\n}\n"
        "Do not include explanations or markdown. Only return JSON.\n\n"
        "Here are the file access stats:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt


def _extract_json(raw: str) -> dict:
    # Remove markdown triple backticks if they exist
    cleaned = re.sub(r"^```json|```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)
