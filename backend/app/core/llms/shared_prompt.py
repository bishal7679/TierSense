# backend/app/core/llms/shared_prompt.py

from app.config import load_tier_ranges

def build_prompt(access_counts: dict) -> str:
    """
    Build a prompt for LLM classification using dynamic tier thresholds.
    """
    ranges = load_tier_ranges()
    hot_min, hot_max = ranges["HOT"]
    warm_min, warm_max = ranges["WARM"]
    cold_min, cold_max = ranges["COLD"]

    prompt = (
        "You are a storage tiering engine.\n"
        "Your job is to classify file paths into one of the following storage tiers based strictly on access frequency:\n"
    )

    # Describe HOT
    if hot_min is not None and hot_max is not None:
        prompt += f"- HOT: Frequently accessed (access_counts ≥ {hot_min} and < {hot_max + 1})\n"
    elif hot_min is not None:
        prompt += f"- HOT: Frequently accessed (access_counts ≥ {hot_min})\n"
    else:
        prompt += "- HOT: Frequently accessed (no lower bound)\n"

    # Describe WARM
    wm_lo = warm_min or 0
    wm_hi = warm_max or "∞"
    prompt += f"- WARM: Occasionally accessed ({wm_lo} ≤ access_counts ≤ {warm_max})\n"

    # Describe COLD
    if cold_max is not None:
        prompt += f"- COLD: Rarely accessed (access_counts ≤ {cold_max})\n"
    else:
        prompt += "- COLD: Rarely accessed (no upper bound)\n"

    prompt += (
        "\nOutput Format Requirements:\n"
        "- Return only a valid JSON object.\n"
        "- Do NOT include explanations, headers, comments, markdown, or natural language.\n"
        "- JSON keys must be the file paths. JSON values must be one of: HOT, WARM, or COLD (uppercase).\n"
        "- Invalid or incomplete output will be rejected.\n\n"
        "=== Access Frequency Data (path: count) ===\n"
    )

    # Provide the raw access counts
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"

    prompt += "\n=== Begin Classification ===\n"
    return prompt
