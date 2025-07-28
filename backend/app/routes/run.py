from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs, parse_logs_for_date
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR
import os
import sqlite3
from datetime import datetime

router = APIRouter()

@router.get("/historical-dates")
async def get_historical_dates():
    """Get list of available dates with historical data"""
    try:
        # Check for existing NDJSON files to determine available dates
        if not os.path.isdir(LOG_DIR):
            return {"available_dates": []}
        
        dates = set()
        for filename in os.listdir(LOG_DIR):
            if filename.endswith(".ndjson") and "tiersense-processed" in filename:
                # Extract date from filename
                if "20250728" in filename:
                    dates.add("2025-07-28")
                # Add more date extraction logic as needed
        
        return {"available_dates": sorted(list(dates), reverse=True)}
    except Exception as e:
        return {"available_dates": []}

@router.post("/generate-historical-heatmap")
async def generate_historical_heatmap(
    date: str = Form(...),
    top_n: int = Form(50),
    directory: str = Form(None)
):
    """Generate heatmap for historical date"""
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "Date must be in YYYY-MM-DD format")
    
    # Determine target directory
    raw = directory.strip() if directory else LOG_DIR
    if raw.startswith("/host-root"):
        target = raw.replace("/host-root", "", 1)
    else:
        target = raw
    
    # Get historical data
    access_counts = parse_logs_for_date(LOG_DIR, date, target)
    if not access_counts:
        raise HTTPException(404, f"No access data found for {date}")
    
    # Generate heatmap
    heatmap_path = generate_heatmap(access_counts, top_n, f"Date: {date}")
    
    return {
        "heatmap": heatmap_path,
        "date": date,
        "total_files": len(access_counts),
        "top_n": min(top_n, len(access_counts))
    }



@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    directory: str = Form(None),
    top_n: int = Form(50)
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
    access_counts = parse_logs(log_dir=LOG_DIR, prefix=target, debug=False)
    if not access_counts:
        raise HTTPException(
            400,
            "No file access events found in logs. "
            "Interact with files under the target directory and try again."
        )

    # Generate heatmap with top N filtering
    heatmap_path = generate_heatmap(access_counts, top_n=top_n)

    # Call LLM for tiering suggestions
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # Helper to strip any remaining /host-root prefix
    def strip_prefix(p: str) -> str:
        return p.replace("/host-root", "", 1) if p.startswith("/host-root") else p

    # Clean analysis entries: strip host-root, remove directories, and deleted files
    analysis = []
    for entry in suggestions.get("analysis", []):
        path = strip_prefix(entry["path"])
        
        # Skip if this is the target directory itself
        if path == target or path.rstrip("/") == target.rstrip("/"):
            continue
            
        # Skip directories (already filtered in parser but double-check)
        if os.path.isdir(path):
            continue
            
        # Skip deleted files (already filtered in parser but double-check)
        if not os.path.exists(path):
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
        "top_n_displayed": min(top_n, len(access_counts))
    })
