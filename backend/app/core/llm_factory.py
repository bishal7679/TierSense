# #llm_factory.py

# import json
# import re
# from app.core.llms import gemini, gpt, claude, copilot, llama, deepseek
# from app.core.llms import llama

# LLM_DISPATCH = {
#     "gemini": gemini.generate,
#     "gpt": gpt.generate,
#     "openai": gpt.generate,           # alias
#     "openrouter": gpt.generate,       # alias
#     "claude": claude.generate,
#     "ollama": llama.generate,
#     "copilot": copilot.generate,
#     "llama": llama.generate,
#     "deepseek": deepseek.generate,
# }

# def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> dict:
#     llm_type = llm_type.lower()

#     if llm_type not in LLM_DISPATCH:
#         raise ValueError(f"Unsupported LLM type: {llm_type}")

#     raw_output = LLM_DISPATCH[llm_type](access_counts)

#     try:
#         # Clean markdown/code fences like ```json ... ```
#         cleaned_output = re.sub(r"```(?:json)?\n?(.*?)```", r"\1", raw_output, flags=re.DOTALL).strip()

#         # Parse the JSON output
#         parsed = json.loads(cleaned_output)

#         summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
#         analysis = []

#         for path, tier in parsed.items():
#             tier_upper = tier.strip().upper()
#             summary["total_files"] += 1
#             if tier_upper == "HOT":
#                 summary["hot_tier"] += 1
#             elif tier_upper == "WARM":
#                 summary["warm_tier"] += 1
#             elif tier_upper == "COLD":
#                 summary["cold_tier"] += 1

#             analysis.append({
#                 "path": path,
#                 "tier": tier_upper,
#                 "score": 0.0,                  # optional placeholder
#                 "access_frequency": "unknown"  # optional for now
#             })

#         return {"summary": summary, "analysis": analysis}

#     except Exception as e:
#         raise ValueError(f"LLM did not return valid JSON: {e}")

import json
import re
from app.core.llms import gemini, gpt, claude, llama, deepseek
from app.core.parser import apply_rule_based_tiering

LLM_DISPATCH = {
    "gemini": gemini.generate,
    "gpt": gpt.generate,
    "openai": gpt.generate,
    "openrouter": gpt.generate,
    "claude": claude.generate,
    "ollama": llama.generate,
    "llama": llama.generate,
    "deepseek": deepseek.generate
}

def generate_tiering_suggestions(llm_type: str, access_counts: dict) -> dict:
    llm_type = llm_type.lower()

    # Option to skip LLM and use rule-based logic only
    if llm_type == "rule":
        return _build_result_from_dict(apply_rule_based_tiering(access_counts))

    if llm_type not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    raw_output = LLM_DISPATCH[llm_type](access_counts)

    try:
        # Clean markdown-style JSON like ```json ... ```
        cleaned_output = re.sub(r"```(?:json)?\n?(.*?)```", r"\1", raw_output, flags=re.DOTALL).strip()

        parsed = json.loads(cleaned_output)
        return _build_result_from_dict(parsed)

    except Exception as e:
        print(f"LLM parsing failed: {e} — Falling back to rule-based logic")
        return _build_result_from_dict(apply_rule_based_tiering(access_counts))

# Shared formatter for both LLM and rule-based responses
def _build_result_from_dict(tiered: dict) -> dict:
    summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
    analysis = []

    for path, tier in tiered.items():
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
            "score": 0.0,
            "access_frequency": "rule" if isinstance(tiered, dict) else "llm"
        })

    return {"summary": summary, "analysis": analysis}
