def build_prompt(access_counts: dict) -> str:
    prompt = (
        "You are a storage tiering engine.\n"
        "Your job is to classify file paths into one of the following storage tiers based strictly on access frequency:\n"
        "- HOT: Frequently accessed (count ≥ 100)\n"
        "- WARM: Occasionally accessed (20 ≤ count < 100)\n"
        "- COLD: Rarely accessed (count < 20)\n\n"
        
        "Output Format Requirements:\n"
        "- Return only a valid JSON object.\n"
        "- Do NOT include explanations, headers, comments, markdown, or natural language.\n"
        "- JSON keys must be the file paths. JSON values must be one of: HOT, WARM, or COLD (uppercase).\n"
        "- Invalid or incomplete output will be rejected.\n\n"
        
        "Example Format:\n"
        "{\n"
        "  \"/mnt/data/file1.txt\": \"HOT\",\n"
        "  \"/mnt/data/file2.csv\": \"WARM\",\n"
        "  \"/mnt/data/archive.zip\": \"COLD\"\n"
        "}\n\n"
        
        "=== Access Frequency Data (path: count) ===\n"
    )

    for path, count in sorted(access_counts.items(), key=lambda x: -x[1]):
        prompt += f"{path}: {count}\n"

    prompt += "\n=== Begin Classification ===\n"
    return prompt