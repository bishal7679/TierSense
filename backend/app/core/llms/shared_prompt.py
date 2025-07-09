def build_prompt(access_counts: dict, max_entries: int = 100) -> str:
    prompt = (
        "You are a storage tiering engine.\n"
        "Your job is to classify file paths into one of the following storage tiers strictly based on access frequency:\n"
        "- HOT: Frequently accessed (access_counts ≥ 100)\n"
        "- WARM: Occasionally accessed (20 ≤ access_counts < 100)\n"
        "- COLD: Rarely accessed (access_counts < 20)\n\n"

        "Output Format Requirements:\n"
        "- Return only a valid JSON object.\n"
        "- Do NOT include explanations, headers, comments, markdown, or natural language.\n"
        "- JSON keys must be the file paths. JSON values must be one of: HOT, WARM, or COLD (uppercase).\n"
        "- Invalid or incomplete output will be rejected.\n\n"

        "Example Format:\n"
        "{\n"
        "  \"/mnt/data/file1.txt\": \"HOT\",\n"
        "  \"/mnt/data/file2.csv\": \"WARM\",\n"
        "}\n\n"

        "=== Access Frequency Data (path: access_counts) ===\n"
    )

    # Sort by access count descending and limit
    top_items = sorted(access_counts.items(), key=lambda x: -x[1])[:max_entries]
    
    for path, count in top_items:
        prompt += f"{path}: {count}\n"

    prompt += "\n=== Begin Classification ===\n"
    return prompt