from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs
from app.core.llm_factory import generateiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR
import os

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    directory: str = Form(None),
):
    # Determine directory input (strip container prefix if present)
    raw = directory.strip() if directory else LOG_DIR
    if raw.startswith("/host-root"):
        target = raw.replace("/host-root", "", 1)
    else:
        target = raw
    target = os.path.realpath(target)

    # Validate path exists inside container
    if not os.path.isdir(raw):
        raise HTTPException(400, f"Directory not found: {raw}")

    # Parse logs under LOG_DIR, filtering by the real host path
    access_counts = parse_logs(log_dir=LOG_DIR, prefix=target)
    if not access_counts:
        raise HTTPException(
            400,
            "No file access events found in logs. "
            "Interact with files under the target directory and try again."
        )

    # Generate heatmap
    heatmap_path = generate_heatmap(access_counts)

    # Call LLM for tiering suggestions
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # Helper to strip any remaining /host-root prefix
    def strip_prefix(p: str) -> str:
        return p.replace("/host-root", "", 1) if p.startswith("/host-root") else p

    # Clean analysis entries: strip host-root and remove exact-match of directory itself
    analysis = []
    for entry in suggestions.get("analysis", []):
        path = strip_prefix(entry["path"])
        if path == target:
            continue
        entry["path"] = path
        analysis.append(entry)

    # Recompute summary counts based on cleaned analysis
    summary = {
        "total_files": len(analysis),
        "hot_tier": sum(1 for e in analysis if e["tier"] == "HOT"),
        "warm_tier": sum(1 for e in analysis if e["tier"] == "WARM"),
        "cold_tier": sum(1 for e in analysis if e["tier"] == "COLD"),
    }

    # Return structured response
    return JSONResponse(content={
        "heatmap": heatmap_path,
        "analysis": analysis,
        "summary": summary,
    })