# #llm_factory.py
# from app.core.llms import gemini, gpt, claude, ollama, copilot

# def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> str:
#     llm_type = llm_type.lower()

#     if llm_type == "gemini":
#         return gemini.generate(access_counts)
#     elif llm_type == "gpt":
#         return gpt.generate(access_counts)
#     elif llm_type == "claude":
#         return claude.generate(access_counts)
#     elif llm_type == "ollama":
#         return ollama.generate(access_counts)
#     elif llm_type == "copilot":
#         return copilot.generate(access_counts)
#     else:
#         raise ValueError(f"Unsupported LLM type: {llm_type}")

import json
import re
from app.core.llms import gemini, gpt, claude, ollama, copilot

def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> dict:
    llm_type = llm_type.lower()

    if llm_type == "gemini":
        raw_output = gemini.generate(access_counts)
    elif llm_type in ["gpt", "openai"]:
        raw_output = gpt.generate(access_counts)
    elif llm_type == "claude":
        raw_output = claude.generate(access_counts)
    elif llm_type == "ollama":
        raw_output = ollama.generate(access_counts)
    elif llm_type == "copilot":
        raw_output = copilot.generate(access_counts)
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    try:
        # 🔧 Clean markdown-like formatting (```json ... ```)
        cleaned_output = re.sub(r"```(?:json)?\n?(.*?)```", r"\1", raw_output, flags=re.DOTALL).strip()

        # 🧪 Attempt to parse as JSON
        parsed = json.loads(cleaned_output)

        summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
        analysis = []

        for path, tier in parsed.items():
            tier_upper = tier.strip().upper()
            summary["total_files"] += 1
            if tier_upper == "HOT":
                summary["hot_tier"] += 1
            elif tier_upper == "WARM":
                summary["warm_tier"] += 1
            elif tier_upper == "COLD":
                summary["cold_tier"] += 1

            analysis.append({
                "path": path,
                "tier": tier_upper,
                "score": 0.0,  # Placeholder if no scoring logic
                "access_frequency": "unknown"  # Optional enhancement
            })

        return {"summary": summary, "analysis": analysis}

    except Exception as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
