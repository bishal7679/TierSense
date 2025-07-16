import os
import json
import re
from app.core.llms import gemini, gpt, claude, llama, deepseek

LLM_DISPATCH = {
    "gemini": gemini.generate,
    "gpt": gpt.generate,
    "openai": gpt.generate,
    "openrouter": gpt.generate,
    "claude": claude.generate,
    "ollama": llama.generate,
    "llama": llama.generate,
    "deepseek": deepseek.generate,
}

def generate_tiering_suggestions(llm_type: str, access_counts: dict, api_key: str = None) -> dict:
    llm_type = llm_type.lower()
    if llm_type not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    try:
        print(f"[+] Invoking LLM: {llm_type}")
        raw_output = LLM_DISPATCH[llm_type](access_counts, api_key)

        # Clean markdown-wrapped JSON blocks (e.g., ```json ... ```)
        cleaned_output = re.sub(r"```(?:json)?\n?(.*?)```", r"\1", raw_output, flags=re.DOTALL).strip()

        parsed = json.loads(cleaned_output)

        summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
        analysis = []

        normalized_counts = {os.path.normpath(k): v for k, v in access_counts.items()}

        for path, tier in parsed.items():
            normalized_path = os.path.normpath(path if path.startswith("/") else f"/{path}")
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
                "score": 0.0,  # Optional: Add confidence score if available from model
                "access_frequency": frequency
            })

        return {
            "summary": summary,
            "analysis": analysis
        }

    except json.JSONDecodeError as e:
        print(f"[!] JSON parsing failed: {e}")
        print(f"LLM raw output:\n{raw_output}")
        raise ValueError(f"LLM returned invalid JSON format: {e}")
    except Exception as e:
        print(f"[!] Error while generating tiering suggestions: {e}")
        raise RuntimeError(f"LLM processing failed: {e}")
