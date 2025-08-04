from app.config import load_tier_ranges

def build_prompt(access_counts: dict) -> str:
    """
    Build an LLM prompt that precisely describes each tier’s inclusive/exclusive bounds,
    using the same wording and numeric intervals as the code and UI.
    """
    ranges = load_tier_ranges()
    hot_min, hot_max = ranges["HOT"]
    warm_min, warm_max = ranges["WARM"]
    cold_min, cold_max = ranges["COLD"]

    prompt = (
        "You are a storage tiering engine.\n"
        "Classify each file into one of three tiers based strictly on access frequency:\n"
    )

    # HOT
    if hot_min is not None and hot_max is not None:
        prompt += f"- HOT: frequently accessed (access_counts ≥ {hot_min} and < {hot_max})\n"
    elif hot_min is not None:
        prompt += f"- HOT: frequently accessed (access_counts ≥ {hot_min})\n"
    else:
        prompt += "- HOT: frequently accessed (no lower bound)\n"

    # WARM
    if warm_min is not None and warm_max is not None:
        prompt += f"- WARM: occasionally accessed (access_counts ≥ {warm_min} and < {warm_max})\n"
    elif warm_min is not None:
        prompt += f"- WARM: occasionally accessed (access_counts ≥ {warm_min})\n"
    elif warm_max is not None:
        prompt += f"- WARM: occasionally accessed (access_counts < {warm_max})\n"
    else:
        prompt += "- WARM: occasionally accessed (no bounds)\n"

    # COLD
    if cold_min is not None and cold_max is not None:
        prompt += f"- COLD: rarely accessed (access_counts ≥ {cold_min} and < {cold_max})\n"
    elif cold_max is not None:
        prompt += f"- COLD: rarely accessed (access_counts < {cold_max})\n"
    else:
        prompt += "- COLD: rarely accessed (no upper bound)\n"

    prompt += (
        "\nOutput format requirements:\n"
        "- Return only a JSON object mapping file paths to HOT, WARM, or COLD.\n"
        "- Do not include any explanatory text, markdown, or extra fields.\n\n"
        "=== Access Frequency Data (path: count) ===\n"
    )

    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"

    prompt += "\n=== Begin Classification ===\n"
    return prompt
