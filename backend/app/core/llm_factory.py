# backend/app/core/llm_factory.py

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
    access_counts: Dict[str,int],
    api_key: str = None
) -> Dict[str,Any]:
    llm = llm_type.lower()
    if llm not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM: {llm}")

    raw = LLM_DISPATCH[llm](access_counts, api_key)
    print(f"[+] Invoking LLM: {llm}")
    print(f"[DEBUG] Raw LLM output:\n{raw}")

    # Strip markdown fences
    cleaned = re.sub(r'^\s*```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'^\s*```(?:json)?', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'```\s*$', '', cleaned, flags=re.MULTILINE)

    # Drop any prefix before first '{'
    i = cleaned.find('{')
    if i>0: cleaned = cleaned[i:]

    # Extract first {...} block (non-greedy)
    m = re.search(r'(\{.*?\})', cleaned, flags=re.DOTALL)
    if m: cleaned = m.group(1)

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        snippet = cleaned[:200].replace('\n',' ')
        print(f"[!] JSON parse error ({e}): {snippet!r}")
        raise ValueError(f"Invalid JSON: {e}")

    if not isinstance(parsed, dict):
        raise ValueError(f"Expected dict, got {type(parsed).__name__}")

    norm = {os.path.normpath(p):c for p,c in access_counts.items()}
    summary = {"total_files":0,"hot_tier":0,"warm_tier":0,"cold_tier":0}
    analysis=[]
    for rp, rt in parsed.items():
        path = os.path.normpath(rp if rp.startswith('/') else f"/{rp}")
        tier = rt.strip().upper()
        if tier not in ("HOT","WARM","COLD"):
            raise ValueError(f"Invalid tier '{rt}' for '{path}'")
        freq = norm.get(path,"unknown")
        summary["total_files"]+=1
        summary[f"{tier.lower()}_tier"]+=1
        analysis.append({"path":path,"tier":tier,"score":0.0,"access_frequency":freq})

    analysis.sort(key=lambda x: norm.get(x["path"],0), reverse=True)
    return {"summary":summary,"analysis":analysis}