from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs, parse_logs_for_date
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR
import os
import sqlite3
from datetime import datetime, timedelta

router = APIRouter()

# Add historical data management
HISTORY_DB = os.path.join(LOG_DIR, "tiersense_history.db")

def init_history_db():
    """Initialize historical data database"""
    os.makedirs(os.path.dirname(HISTORY_DB), exist_ok=True)
    with sqlite3.connect(HISTORY_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_access_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                file_path TEXT NOT NULL,
                access_count INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, file_path)
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_access_counts(date)")

@router.get("/historical-dates")
async def get_historical_dates():
    """Get list of available dates with historical data"""
    try:
        init_history_db()
        with sqlite3.connect(HISTORY_DB) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT date FROM daily_access_counts 
                ORDER BY date DESC LIMIT 30
            """)
            dates = [row[0] for row in cursor.fetchall()]
        
        # Also check for direct NDJSON files
        if os.path.isdir(LOG_DIR):
            for filename in os.listdir(LOG_DIR):
                if filename.endswith(".ndjson") and "tiersense-processed" in filename:
                    if "2025-07-28" in filename or "20250728" in filename:
                        if "2025-07-28" not in dates:
                            dates.append("2025-07-28")
        
        return {"available_dates": sorted(list(set(dates)), reverse=True)}
    except Exception as e:
        print(f"Error fetching dates: {e}")
        return {"available_dates": []}

@router.post("/search-heatmaps")
async def search_heatmaps(
    search_type: str = Form(...),  # "current", "date", "range", "pattern"
    date: str = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
    file_pattern: str = Form(None),
    top_n: int = Form(50),
    directory: str = Form(None)
):
    """Advanced search for heatmaps with multiple filter options"""
    
    # Determine target directory
    raw = directory.strip() if directory else LOG_DIR
    if raw.startswith("/host-root"):
        target = raw.replace("/host-root", "", 1)
    else:
        target = raw
    target = os.path.realpath(target)

    access_counts = {}
    title_suffix = ""
    
    try:
        if search_type == "current":
            # Current day analysis
            access_counts = parse_logs(log_dir=LOG_DIR, prefix=target)
            title_suffix = f"Today ({datetime.now().strftime('%Y-%m-%d')})"
            
        elif search_type == "date" and date:
            # Single date analysis
            access_counts = parse_logs_for_date(LOG_DIR, date, target)
            title_suffix = f"Date: {date}"
            
        elif search_type == "range" and start_date and end_date:
            # Date range analysis - aggregate multiple days
            init_history_db()
            with sqlite3.connect(HISTORY_DB) as conn:
                cursor = conn.execute("""
                    SELECT file_path, SUM(access_count) as total_access
                    FROM daily_access_counts 
                    WHERE date BETWEEN ? AND ? AND file_path LIKE ?
                    GROUP BY file_path
                    ORDER BY total_access DESC
                """, (start_date, end_date, f"{target}%"))
                access_counts = dict(cursor.fetchall())
            title_suffix = f"Range: {start_date} to {end_date}"
            
        elif search_type == "pattern":
            # Pattern-based search
            access_counts = parse_logs(log_dir=LOG_DIR, prefix=target)
            if file_pattern:
                # Filter by pattern
                filtered_counts = {}
                for path, count in access_counts.items():
                    if file_pattern.lower() in path.lower():
                        filtered_counts[path] = count
                access_counts = filtered_counts
                title_suffix = f"Pattern: {file_pattern}"
        
        if not access_counts:
            raise HTTPException(404, f"No data found for the specified search criteria")
        
        # Apply top N filtering
        sorted_items = sorted(access_counts.items(), key=lambda x: x[1], reverse=True)
        top_items = dict(sorted_items[:top_n])
        
        # Generate heatmap
        heatmap_path = generate_heatmap(top_items, top_n, title_suffix)
        
        return {
            "heatmap": heatmap_path,
            "search_type": search_type,
            "total_files": len(access_counts),
            "displayed_files": len(top_items),
            "top_n": top_n,
            "title": title_suffix
        }
        
    except Exception as e:
        raise HTTPException(500, f"Search failed: {str(e)}")

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    directory: str = Form(None),
    top_n: int = Form(50)
):
    """Enhanced run tiering with immediate heatmap generation and historical storage"""
    
    # Determine directory input
    raw = directory.strip() if directory else LOG_DIR
    if raw.startswith("/host-root"):
        target = raw.replace("/host-root", "", 1)
    else:
        target = raw
    target = os.path.realpath(target)

    # Validate directory
    if not os.path.isdir(raw):
        raise HTTPException(400, f"Directory not found: {raw}")

    # Parse logs
    access_counts = parse_logs(log_dir=LOG_DIR, prefix=target, debug=False)
    if not access_counts:
        raise HTTPException(
            400,
            "No file access events found in logs. "
            "Interact with files under the target directory and try again."
        )

    # Generate immediate heatmap
    today = datetime.now().strftime("%Y-%m-%d")
    heatmap_path = generate_heatmap(access_counts, top_n=top_n, title_suffix=f"Today ({today})")

    # Store historical data
    init_history_db()
    with sqlite3.connect(HISTORY_DB) as conn:
        for file_path, count in access_counts.items():
            conn.execute("""
                INSERT OR REPLACE INTO daily_access_counts 
                (date, file_path, access_count) VALUES (?, ?, ?)
            """, (today, file_path, count))

    # Generate LLM analysis
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # Clean analysis entries
    def strip_prefix(p: str) -> str:
        return p.replace("/host-root", "", 1) if p.startswith("/host-root") else p

    analysis = []
    for entry in suggestions.get("analysis", []):
        path = strip_prefix(entry["path"])
        
        if path == target or path.rstrip("/") == target.rstrip("/"):
            continue
        if os.path.isdir(path):
            continue
        if not os.path.exists(path):
            continue
            
        entry["path"] = path
        analysis.append(entry)

    # Recompute summary
    summary = {
        "total_files": len(analysis),
        "hot_tier": sum(1 for e in analysis if e["tier"] == "HOT"),
        "warm_tier": sum(1 for e in analysis if e["tier"] == "WARM"),
        "cold_tier": sum(1 for e in analysis if e["tier"] == "COLD"),
    }

    return JSONResponse(content={
        "heatmap": heatmap_path,
        "analysis": analysis,
        "summary": summary,
        "top_n_displayed": min(top_n, len(access_counts)),
        "search_enabled": True  # Flag to enable search UI
    })
