import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate(access_counts: dict) -> str:
    if not access_counts:
        return "No access data provided."

    prompt = _build_prompt(access_counts)
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Claude API error: {e}"

def _build_prompt(access_counts):
    prompt = (
        "You're a storage policy engine.\n"
        "Return JSON classifying paths into HOT/WARM/COLD tiers based on frequency.\n\n"
    )
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"
    return prompt
