# #gemini.py
# import os
# import google.generativeai as genai

# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# def generate(access_counts: dict) -> str:
#     if not access_counts:
#         return "No access data provided."

#     prompt = _build_prompt(access_counts)
#     try:
#         model = genai.GenerativeModel("models/gemini-2.0-pro")
#         response = model.generate_content(prompt)
#         return response.text.strip()
#     except Exception as e:
#         return f"Gemini API error: {e}"

# def _build_prompt(access_counts):
#     prompt = (
#         "Classify the following file paths into storage tiers:\n"
#         "- HOT: Frequently accessed\n"
#         "- WARM: Moderately accessed\n"
#         "- COLD: Rarely accessed\n\n"
#         "Respond in JSON format only.\n\n"
#     )
#     for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
#         prompt += f"{path}: {count}\n"
#     return prompt
import os
import google.generativeai as genai

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    # Re-configure Gemini with the correct API key at runtime
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API error: Missing GEMINI_API_KEY environment variable."

    try:
        genai.configure(api_key=api_key)

        prompt = _build_prompt(access_counts)
        model = genai.GenerativeModel("models/gemini-2.0-pro")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Gemini API error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "Classify the following file paths into storage tiers:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Moderately accessed\n"
        "- COLD: Rarely accessed\n\n"
        "Respond in JSON format only.\n\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt
