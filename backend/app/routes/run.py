from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
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
    # Determine directory
    target = directory.strip() if directory else LOG_DIR
    target = os.path.realpath(target)

    if not os.path.isdir(target):
        raise HTTPException(400, f"Directory not found: {target}")

    # Parse logs (returns only access_counts)
    access_counts = parse_logs(log_dir=LOG_DIR, prefix=target)


    if not access_counts:
        raise HTTPException(400, "No file access events found in logs. Interact with files and try again.")

    # Generate heatmap and capture its path
    heatmap_path = generate_heatmap(access_counts)

    # Call LLM for tiering suggestions
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # Return combined response
    return JSONResponse(content={
        "heatmap": heatmap_path,
        "analysis": suggestions.get("analysis", []),
        "summary": suggestions.get("summary", []),
    })
