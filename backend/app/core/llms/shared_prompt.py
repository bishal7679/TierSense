from app.config import load_tier_ranges

def build_prompt(access_counts: dict) -> str:
    """
    Build the LLM prompt using dynamic, user-configurable tier ranges.
    """
    ranges = load_tier_ranges()
    prompt = (
        "You are a storage tiering engine.\n"
        "Your job is to classify file paths into one of the following storage tiers based strictly on access frequency:\n"
    )
    for tier, (min_v, max_v) in ranges.items():
        if min_v is not None and max_v is not None:
            prompt += f"- {tier}: {min_v} ≤ access_counts < {max_v}\n"
        elif min_v is not None:
            prompt += f"- {tier}: access_counts ≥ {min_v}\n"
        elif max_v is not None:
            prompt += f"- {tier}: access_counts < {max_v}\n"
        else:
            prompt += f"- {tier}: no bounds (all values)\n"

    prompt += (
        "\n"
        "Output Format Requirements:\n"
        "- Return only a valid JSON object.\n"
        "- Do NOT include explanations, headers, comments, markdown, or natural language.\n"
        "- JSON keys must be the file paths. JSON values must be one of: HOT, WARM, or COLD (uppercase).\n"
        "- Invalid or incomplete output will be rejected.\n\n"
        "=== Access Frequency Data (path: count) ===\n"
    )

    # Sort by highest access count to prioritize hot files in context
    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"

    prompt += "\n=== Begin Classification ===\n"
    return prompt