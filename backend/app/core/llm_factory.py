import os, json, re
from typing import Dict, Any
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

def generate_tiering_suggestions(
    llm_type: str,
    access_counts: Dict[str, int],
    api_key: str = None
) -> Dict[str, Any]:
    llm_type = llm_type.lower()
    if llm_type not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm_type}")

    # 1. Invoke LLM
    print(f"[+] Invoking LLM: {llm_type}")
    raw_output = LLM_DISPATCH[llm_type](access_counts, api_key)
    print(f"[DEBUG] Raw LLM output:\n{raw_output}")

    # 2. Strip markdown code fences
    cleaned = re.sub(r'^\s*```', '', raw_output.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)

    # 3. Extract first {...} JSON block if extra text remains
    match = re.search(r"(\{.*\})", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    # 4. Parse JSON
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        snippet = cleaned[:200].replace("\n", " ")
        print(f"[!] Failed to parse JSON ({e}): {snippet!r}")
        raise ValueError(f"LLM returned invalid JSON format: {e}")

    # 5. Validate structure
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")

    # 6. Build summary and analysis
    normalized_counts = {os.path.normpath(p): cnt for p, cnt in access_counts.items()}
    summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
    analysis = []

    for raw_path, raw_tier in parsed.items():
        path = os.path.normpath(raw_path if raw_path.startswith("/") else f"/{raw_path}")
        tier = raw_tier.strip().upper()
        if tier not in ("HOT", "WARM", "COLD"):
            raise ValueError(f"Invalid tier '{raw_tier}' for path '{path}'")

        freq = normalized_counts.get(path, "unknown")
        summary["total_files"] += 1
        summary[f"{tier.lower()}_tier"] += 1

        analysis.append({
            "path": path,
            "tier": tier,
            "score": 0.0,
            "access_frequency": freq
        })

    # 7. Sort analysis by descending access count
    analysis.sort(key=lambda x: normalized_counts.get(x["path"], 0), reverse=True)

    return {"summary": summary, "analysis": analysis}
