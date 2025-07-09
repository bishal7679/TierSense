import json
import re
import os
from app.core.llms import gemini, gpt, claude, llama, deepseek

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

    if llm_type not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    raw_output = LLM_DISPATCH[llm_type](access_counts)

    try:
        # Clean markdown/code fences like ```json ... ```
        cleaned_output = re.sub(r"```(?:json)?\n?(.*?)```", r"\1", raw_output, flags=re.DOTALL).strip()

        # Parse the JSON output
        parsed = json.loads(cleaned_output)

        # Normalize access_counts keys once
        normalized_access_counts = {os.path.normpath(k): v for k, v in access_counts.items()}

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

            # ✅ Normalize path before matching
            normalized_path = os.path.normpath(path)
            frequency = normalized_access_counts.get(normalized_path, "unknown")

            analysis.append({
                "path": path,
                "tier": tier_upper,
                "score": 0.0,
                "access_frequency": frequency
            })

        return {"summary": summary, "analysis": analysis}

    except Exception as e:
        raise ValueError(f"LLM did not return valid JSON: {e}")
