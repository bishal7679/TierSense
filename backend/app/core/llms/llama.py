import requests
import json

OLLAMA_API_URL = "http://localhost:11434/api/generate"

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={"model": "llama3", "prompt": prompt, "stream": False}
        )
        if response.status_code == 200:
            return response.json()["response"].strip()
        return f"Ollama error: {response.text}"
    except Exception as e:
        return f"Ollama request failed: {e}"

def _build_prompt(access_counts):
    prompt = (
        "Classify paths into HOT, WARM, or COLD tiers based on access frequency.\n"
        "Respond only with valid JSON.\n\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt
