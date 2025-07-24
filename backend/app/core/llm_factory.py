import os
import json
import re
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
    llm = llm_type.lower()
    if llm not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm}")

    # 1. Invoke LLM
    raw = LLM_DISPATCH[llm](access_counts, api_key)
    print(f"[+] Invoking LLM: {llm}")
    print(f"[DEBUG] Raw LLM output:\n{raw}")

    # 2. Strip markdown code fences (``````json)
    # 2. Strip markdown code fences (```json ... ```)
    cleaned = raw
    cleaned = re.sub(r'^\s*```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)


    # 3. Remove any leading non-JSON text (e.g., stray "json ")
    first_brace = cleaned.find('{')
    if first_brace > 0:
        cleaned = cleaned[first_brace:]

    # 4. Balance braces if truncated
    open_braces = cleaned.count('{')
    close_braces = cleaned.count('}')
    if close_braces < open_braces:
        cleaned += '}' * (open_braces - close_braces)

    # 5. Extract the first complete JSON object (non-greedy)
    match = re.search(r'(\{.*?\})', cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1)

    # 6. Parse JSON
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        snippet = cleaned[:200].replace('\n', ' ')
        print(f"[!] JSON parse error ({e}): {snippet!r}")
        raise ValueError(f"LLM returned invalid JSON format: {e}")

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")

    # 7. Build summary and analysis
    norm = {os.path.normpath(p): cnt for p, cnt in access_counts.items()}
    summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
    analysis = []

    for raw_path, raw_tier in parsed.items():
        path = os.path.normpath(raw_path if raw_path.startswith('/') else f"/{raw_path}")
        tier = raw_tier.strip().upper()
        if tier not in ("HOT", "WARM", "COLD"):
            raise ValueError(f"Invalid tier '{raw_tier}' for path '{path}'")
        freq = norm.get(path, "unknown")
        summary["total_files"] += 1
        summary[f"{tier.lower()}_tier"] += 1
        analysis.append({
            "path": path,
            "tier": tier,
            "score": 0.0,
            "access_frequency": freq
        })

    # 8. Sort by descending access count
    analysis.sort(key=lambda x: norm.get(x["path"], 0), reverse=True)

    return {"summary": summary, "analysis": analysis}