import os
import json
import re
from typing import Dict, Any
from datetime import datetime
from app.core.llms import gemini, gpt, claude, llama, deepseek
LLM_DISPATCH = {
    "gemini": lambda counts, key, **kw: gemini.generate(counts, key),
    "gpt":    lambda counts, key, **kw: gpt.generate(counts, key, model=kw.get("model")),
    "openai": lambda counts, key, **kw: gpt.generate(counts, key, model=kw.get("model")),
    "openrouter": lambda counts, key, **kw: gpt.generate(counts, key, model=kw.get("model")),  # kept for backward-compat
    "claude": lambda counts, key, **kw: claude.generate(counts, key, model=kw.get("model")),
    "ollama": lambda counts, key, **kw: llama.generate(counts, key, model=kw.get("model"), base_url=kw.get("base_url")),
    "llama":  lambda counts, key, **kw: llama.generate(counts, key, model=kw.get("model"), base_url=kw.get("base_url")),
    "deepseek": lambda counts, key, **kw: deepseek.generate(counts, key, model=kw.get("model")),
}


def generate_tiering_suggestions(
    llm_type: str,
    access_counts: Dict[str, int],
    api_key: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    1. Call the selected LLM to classify files into tiers.
    2. Clean and parse the JSON response.
    3. Enrich each file entry with dynamic suggestions and metadata.

    kwargs:
      - model: optional model name for gpt/claude/llama/deepseek adapters
      - base_url: optional OpenAI-compatible base URL for llama adapter
    """
    llm = llm_type.lower()
    if llm not in LLM_DISPATCH:
        raise ValueError(f"Unsupported LLM type: {llm}")

    # 1. Invoke LLM (pass through optional model/base_url without breaking callers)
    raw = LLM_DISPATCH[llm](access_counts, api_key, **kwargs)
    print(f"[+] Invoking LLM: {llm}")
    print(f"[DEBUG] Raw LLM output:\n{raw}")

    # 2. Strip markdown fences
    cleaned = raw
    cleaned = re.sub(r'^\s*```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)

    # 3. Trim leading non-JSON text
    idx = cleaned.find('{')
    if idx > 0:
        cleaned = cleaned[idx:]

    # 4. Balance braces
    open_b = cleaned.count('{')
    close_b = cleaned.count('}')
    if close_b < open_b:
        cleaned += '}' * (open_b - close_b)

    # 5. Extract first JSON object
    match = re.search(r'(\{.*?\})', cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1)

    # 6. Parse JSON
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        snippet = cleaned[:200].replace('\n', ' ')
        print(f"[!] JSON parse error ({e}): {snippet!r}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    if not isinstance(parsed, dict):
        raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")

    # 7. Normalize and build analysis entries
    normalized = {os.path.normpath(p): cnt for p, cnt in access_counts.items()}
    summary = {"total_files": 0, "hot_tier": 0, "warm_tier": 0, "cold_tier": 0}
    raw_analysis = []

    for raw_path, raw_tier in parsed.items():
        path = os.path.normpath(raw_path if raw_path.startswith('/') else f"/{raw_path}")
        tier = raw_tier.strip().upper()
        if tier not in ("HOT", "WARM", "COLD"):
            raise ValueError(f"Invalid tier '{raw_tier}' for path '{path}'")
        freq = normalized.get(path, 0)
        summary["total_files"] += 1
        summary[f"{tier.lower()}_tier"] += 1
        raw_analysis.append({
            "path": path,
            "tier": tier,
            "access_frequency": freq,
        })

    # 8. Sort by frequency descending
    raw_analysis.sort(key=lambda x: x["access_frequency"], reverse=True)

    # 9. Enrich each entry with suggestion & metadata
    enriched = _attach_suggestions_and_metadata(raw_analysis, normalized)

    return {"summary": summary, "analysis": enriched}


def _attach_suggestions_and_metadata(analysis, access_counts):
    """For each file, add a context-aware suggestion and filesystem metadata."""
    return [
        {
            **item,
            "suggestion": _generate_suggestion(item, access_counts),
            "metadata": _get_file_metadata(item["path"]),
        }
        for item in analysis
    ]


def _generate_suggestion(item, all_counts) -> str:
    """Return a tailored recommendation based on tier, frequency, and file context."""
    tier = item["tier"]
    freq = item["access_frequency"]
    sorted_vals = sorted(all_counts.values(), reverse=True)
    percentile = sorted_vals.index(freq) / max(1, len(sorted_vals)) * 100 if freq in sorted_vals else 0.0

    ext = os.path.splitext(item["path"])[1].lower()

    if tier == "HOT":
        if freq >= 200:
            return (
                f"🔥 Very high demand ({freq} accesses, top {percentile:.0f}%). "
                "Use SSD caching or CDN distribution for optimum performance."
            )
        if ext in (".db", ".sql"):
            return "💾 High-activity database file—consider read replicas & indexing."
        return "⚡ Keep on premium storage; monitor for caching opportunities."
    if tier == "WARM":
        if ext in (".log", ".txt"):
            return "📝 Active log—enable rotation and compress older entries."
        return "📊 Standard cloud tier is cost-effective for this access pattern."
    # COLD
    if freq < 10:
        return "❄️ Rarely accessed—archive to deep storage for maximum savings."
    return "💤 Low usage—apply automated lifecycle rules to archive after 30 days."


def _get_file_metadata(path: str) -> Dict[str, Any]:
    """Retrieve file size and last modification date; best-effort."""
    try:
        st = os.stat(path)
        return {
            "size_mb": round(st.st_size / (1024**2), 2),
            "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
            "type": os.path.splitext(path)[1] or "unknown"
        }
    except Exception:
        return {"size_mb": None, "modified": None, "type": None}
