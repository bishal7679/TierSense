import os
import json
import re
from app.core.llms import gemini, gpt, claude, llama, deepseek

LLM_DISPATCH = {
    "gemini": gemini.generate,
    "gpt": gpt.generate,
    "openai": gpt.generate,
    "claude": claude.generate,
    "llama": llama.generate,
    "deepseek": deepseek.generate,
}

def _extract_json_from_response(raw_text: str) -> dict:
    """
    A robust function to find and parse a JSON object from a raw text response.
    It handles markdown code fences (```json ... ```) and other surrounding text.
    """
    # Find the start of the JSON object
    json_start_index = raw_text.find('{')
    if json_start_index == -1:
        raise ValueError("LLM response did not contain a valid JSON object.")

    # Find the end of the JSON object by matching braces
    json_end_index = -1
    open_braces = 0
    for i, char in enumerate(raw_text[json_start_index:]):
        if char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
        
        if open_braces == 0:
            json_end_index = json_start_index + i + 1
            break
    
    if json_end_index == -1:
        raise ValueError("LLM response contained an incomplete JSON object.")

    # Extract the JSON string and parse it
    json_string = raw_text[json_start_index:json_end_index]
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse extracted JSON: {e}")


def generate_tiering_suggestions(llm_type: str, access_counts: dict, api_key: str = None) -> dict:
    llm_type = llm_type.lower()
    if llm_type not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    try:
        print(f"[+] Invoking LLM: {llm_type}")
        raw_output = LLM_DISPATCH[llm_type](access_counts, api_key)

        # Use the new, robust function to clean and parse the output
        parsed_json = _extract_json_from_response(raw_output)

        summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
        analysis = []

        normalized_counts = {os.path.normpath(k): v for k, v in access_counts.items()}

        for path, tier in parsed_json.items():
            normalized_path = os.path.normpath(path)
            frequency = normalized_counts.get(normalized_path, "unknown")

            tier_upper = tier.strip().upper()
            summary["total_files"] += 1
            if tier_upper == "HOT":
                summary["hot_tier"] += 1
            elif tier_upper == "WARM":
                summary["warm_tier"] += 1
            elif tier_upper == "COLD":
                summary["cold_tier"] += 1

            analysis.append({
                "path": normalized_path,
                "tier": tier_upper,
                "access_frequency": frequency
            })

        return {
            "summary": summary,
            "analysis": analysis
        }

    except Exception as e:
        print(f"[!] Error during tiering suggestion: {e}")
        # Re-raise as a runtime error to be caught by the API route
        raise RuntimeError(f"LLM processing failed: {e}")

