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
        "HTTP-Referer": "https://your-project-site.com",
        "X-Title": "TierSense"
    }

    payload = {
        "model": "meta-llama/llama-3-8b-instruct:free",  # ✅ Free model
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        if "choices" not in data or not data["choices"]:
            return f"⚠️ OpenRouter returned invalid structure: {data}"

        raw = data["choices"][0]["message"]["content"]

        print("🔍 LLaMA raw response (first 100 chars):", repr(raw[:100]))  # Preview
        return _extract_json(raw)

    except requests.RequestException as req_err:
        return f"LLaMA API error (HTTP): {req_err}"
    except ValueError as parse_err:
        return f"LLaMA response parsing error: {parse_err}"
    except Exception as e:
        return f"LLaMA unexpected error: {e}"


def _build_prompt(access_counts: dict) -> str:
    prompt = (
        "You are a file tiering assistant.\n"
        "Classify each file path into one of these tiers based on frequency:\n"
        "- HOT: Frequently accessed\n"
        "- WARM: Occasionally accessed\n"
        "- COLD: Rarely accessed\n\n"
        "**Important**: Return ONLY valid JSON. No comments. No markdown. No explanation.\n"
        "Example:\n"
        "{\n  \"/mnt/data/file1.txt\": \"HOT\",\n  \"/mnt/data/file2.txt\": \"COLD\"\n}\n\n"
        "Now classify the following:\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt


def _extract_json(raw: str) -> str:
    # ✅ Save raw output to file for debug inspection
    try:
        with open("/home/ubuntu/llm_raw_output.log", "w") as f:
            f.write(raw)
    except Exception as log_err:
        print(f"⚠️ Failed to write raw output to log: {log_err}")

    # ✅ Strip markdown-style ```json``` if present
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw).strip()

    try:
        parsed = json.loads(cleaned)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
