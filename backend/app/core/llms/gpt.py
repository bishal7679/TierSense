import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"OpenAI GPT error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "You're a storage optimization system.\n"
        "Classify paths as HOT/WARM/COLD based on access frequency.\n"
        "Return valid JSON.\n\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt
