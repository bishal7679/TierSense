def build_prompt(access_counts: dict) -> str:
    prompt = (
        "You are a storage tiering engine.\n"
        "Your job is to classify file paths into one of the following storage tiers based strictly on access frequency:\n"
        "- HOT: Frequently accessed (access_counts ≥ 100)\n"
        "- WARM: Occasionally accessed (20 ≤ access_counts < 100)\n"
        "- COLD: Rarely accessed (access_counts < 20)\n\n"
        
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