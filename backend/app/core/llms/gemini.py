import google.generativeai as genai
from app.core.llms.shared_prompt import build_prompt

def generate(access_counts: dict, api_key: str) -> str:
    if not access_counts:
        return "No access data provided."

    if not api_key:  # No fallback to env
        raise ValueError("Gemini API error: API key is required but missing.")

    try:
        genai.configure(api_key=api_key)

        prompt = build_prompt(access_counts)
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)

        if not response or not hasattr(response, "text"):
            raise ValueError("Gemini API returned an invalid response.")

        return response.text.strip()

    except Exception as e:
        raise ValueError(f"Gemini API error: {e}")