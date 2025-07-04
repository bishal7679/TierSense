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
from app.core.llms import gemini, gpt, claude, ollama, copilot

def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> dict:
    llm_type = llm_type.lower()

    if llm_type == "gemini":
        raw_output = gemini.generate(access_counts)
    elif llm_type == "gpt":
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
        parsed = json.loads(raw_output)
        summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
        analysis = []

        for path, tier in parsed.items():
            tier_upper = tier.upper()
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
                "score": 0.0,  # You can replace with actual score if needed
                "access_frequency": "unknown"  # Replace with logic if available
            })

        return {"summary": summary, "analysis": analysis}

    except json.JSONDecodeError:
        raise ValueError("LLM did not return valid JSON")
