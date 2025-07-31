from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import (
    parse_logs,
    parse_logs_for_date,
    parse_logs_with_daily_reset
)
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap, cleanup_old_heatmaps
from app.core.daily_reset import manual_reset
from app.core.historical import historical_manager
from app.config import LOG_DIR, HEATMAP_PATH
import os
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

HISTORY_DB = os.path.join(LOG_DIR, "tiersense_history.db")

def init_history_db():
    """Initialize SQLite database for daily reset historical data tables."""
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_files INTEGER NOT NULL,
                max_access_count INTEGER NOT NULL,
                min_access_count INTEGER NOT NULL,
                avg_access_count REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_access_counts(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON daily_access_counts(file_path)")

@router.get("/historical-dates")
async def get_historical_dates():
    """Get list of available dates with daily-reset historical data."""
    try:
        init_history_db()
        with sqlite3.connect(HISTORY_DB) as conn:
            rows = conn.execute("""
                SELECT DISTINCT date FROM daily_access_counts
                ORDER BY date DESC
                LIMIT 30
            """).fetchall()
        dates = [row[0] for row in rows]
        if os.path.isdir(LOG_DIR):
            for fn in os.listdir(LOG_DIR):
                if fn.startswith("tiersense-processed") and fn.endswith(".ndjson"):
                    # Extract date from filename patterns
                    if "2025-07-31" in fn and "2025-07-31" not in dates:
                        dates.append("2025-07-31")
                    elif "20250731" in fn and "2025-07-31" not in dates:
                        dates.append("2025-07-31")
        return {"available_dates": sorted(set(dates), reverse=True)}
    except Exception as e:
        logger.error(f"Error fetching historical dates: {e}")
        return {"available_dates": []}

@router.post("/search-heatmaps")
async def search_heatmaps(
    search_type: str = Form(...),
    date: str = Form(None),
    start_date: str = Form(None),
    end_date: str = Form(None),
    file_pattern: str = Form(None),
    top_n: int = Form(50),
    directory: str = Form(None)
):
    """Advanced heatmap search with daily-reset support."""
    raw = directory.strip() if directory else LOG_DIR
    target = raw.replace("/host-root", "", 1) if raw.startswith("/host-root") else raw
    target = os.path.realpath(target)

    try:
        # CRITICAL FIX: Purge old heatmaps before any search operation
        hm_dir = os.path.dirname(HEATMAP_PATH)
        if os.path.isdir(hm_dir):
            for fname in os.listdir(hm_dir):
                if fname.startswith("access_heatmap_") and fname.endswith(".png"):
                    try:
                        os.remove(os.path.join(hm_dir, fname))
                    except Exception:
                        pass

        if search_type == "current":
            access_counts = parse_logs_with_daily_reset(LOG_DIR, prefix=target, debug=False)
            title = f"Today ({datetime.now().strftime('%Y-%m-%d')}) - Daily Reset"
        elif search_type == "date" and date:
            data = historical_manager.get_daily_reset_data(date)
            if data:
                access_counts = data["access_counts"]
                title = f"Date: {date} (Daily Reset)"
            else:
                access_counts = parse_logs_for_date(LOG_DIR, date, target)
                title = f"Date: {date}"
        elif search_type == "range" and start_date and end_date:
            init_history_db()
            daily_data = {}
            with sqlite3.connect(HISTORY_DB) as conn:
                for d, fp, cnt in conn.execute("""
                    SELECT date, file_path, access_count
                    FROM daily_access_counts
                    WHERE date BETWEEN ? AND ? AND file_path LIKE ?
                    ORDER BY date DESC, access_count DESC
                """, (start_date, end_date, f"{target}%")):
                    daily_data.setdefault(d, {})[fp] = cnt
            if daily_data:
                latest = max(daily_data)
                access_counts = daily_data[latest]
                title = f"Latest from Range: {latest} (Daily Reset)"
            else:
                access_counts = {}
                title = ""
        elif search_type == "pattern":
            access_counts = parse_logs_with_daily_reset(LOG_DIR, prefix=target, debug=False)
            if file_pattern:
                access_counts = {
                    p: c for p, c in access_counts.items()
                    if file_pattern.lower() in p.lower()
                }
            title = f"Pattern: {file_pattern} (Daily Reset)"
        else:
            access_counts = {}
            title = ""

        if not access_counts:
            raise HTTPException(404, "No data found for the specified search criteria")

        # CRITICAL FIX: Calculate tier summary directly from access_counts for search-heatmaps
        hot_tier = sum(1 for count in access_counts.values() if count >= 100)
        warm_tier = sum(1 for count in access_counts.values() if 20 <= count < 100)
        cold_tier = sum(1 for count in access_counts.values() if count < 20)

        top_items = dict(sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
        heatmap = generate_heatmap(top_items, top_n, title)
        return {
            "heatmap": heatmap,
            "search_type": search_type,
            "total_files": len(access_counts),
            "displayed_files": len(top_items),
            "top_n": top_n,
            "title": title,
            "daily_reset": True,
            # CRITICAL FIX: Return tier counts in search-heatmaps response
            "hot_tier": hot_tier,
            "warm_tier": warm_tier,
            "cold_tier": cold_tier
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, f"Search failed: {e}")

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    directory: str = Form(None),
    top_n: int = Form(50)
):
    """Run tiering analysis with daily-reset fresh counts."""
    raw = directory.strip() if directory else LOG_DIR
    target = raw.replace("/host-root", "", 1) if raw.startswith("/host-root") else raw
    target = os.path.realpath(target)
    if not os.path.isdir(raw):
        raise HTTPException(400, f"Directory not found: {raw}")

    # CRITICAL FIX: Purge ALL old heatmaps before generating a new one
    hm_dir = os.path.dirname(HEATMAP_PATH)
    if os.path.isdir(hm_dir):
        for fname in os.listdir(hm_dir):
            if fname.startswith("access_heatmap_") and fname.endswith(".png"):
                try:
                    os.remove(os.path.join(hm_dir, fname))
                    logger.info(f"Removed old heatmap before analysis: {fname}")
                except Exception:
                    pass

    today = datetime.now().strftime("%Y-%m-%d")
    access_counts = parse_logs_with_daily_reset(LOG_DIR, prefix=target, debug=False)
    if not access_counts:
        raise HTTPException(
            400,
            f"No file access events found in today's logs ({today}). Interact with files and retry."
        )

    # Generate single fresh heatmap
    heatmap = generate_heatmap(access_counts, top_n=top_n, title_suffix=f"Today ({today}) - Daily Reset")

    # Save historical data and cleanup
    historical_manager.save_daily_reset_data(today, access_counts)
    historical_manager.cleanup_old_reset_data(days_to_keep=7)
    
    # FIXED: Only keep 1 heatmap instead of 7 to prevent accumulation
    cleanup_old_heatmaps(keep_count=1)

    # LLM analysis
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # CRITICAL FIX: Calculate tier summary directly from access_counts BEFORE filtering
    hot_tier = sum(1 for count in access_counts.values() if count >= 100)
    warm_tier = sum(1 for count in access_counts.values() if 20 <= count < 100)
    cold_tier = sum(1 for count in access_counts.values() if count < 20)

    def strip_pref(p: str) -> str:
        return p.replace("/host-root", "", 1) if p.startswith("/host-root") else p

    analysis = []
    for ent in suggestions.get("analysis", []):
        path = strip_pref(ent["path"])
        if path == target or not os.path.exists(path) or os.path.isdir(path):
            continue
        ent["path"] = path
        analysis.append(ent)

    # CRITICAL FIX: Use calculated tier counts from access_counts instead of filtered analysis
    summary = {
        "total_files": len(access_counts),  # Use access_counts for total, not filtered analysis
        "hot_tier": hot_tier,              # Use calculated counts from access_counts
        "warm_tier": warm_tier,            # Use calculated counts from access_counts
        "cold_tier": cold_tier,            # Use calculated counts from access_counts
    }

    return JSONResponse({
        "heatmap": heatmap,
        "analysis": analysis,
        "summary": summary,
        "top_n_displayed": min(top_n, len(access_counts)),
        "search_enabled": True,
        "daily_reset": True,
        "reset_time": "00:00",
        "date": today,
        "message": f"Daily reset: Access counts started fresh for {today}"
    })

@router.post("/manual-reset")
async def trigger_manual_reset():
    """Manually trigger daily reset for testing."""
    try:
        logger.info("Manual reset triggered via API")
        
        # CRITICAL FIX: Purge all heatmaps before reset
        hm_dir = os.path.dirname(HEATMAP_PATH)
        if os.path.isdir(hm_dir):
            for fname in os.listdir(hm_dir):
                if fname.startswith("access_heatmap_") and fname.endswith(".png"):
                    try:
                        os.remove(os.path.join(hm_dir, fname))
                        logger.info(f"Removed heatmap during manual reset: {fname}")
                    except Exception:
                        pass
        
        manual_reset()
        return {
            "status": "success",
            "message": "Daily reset completed successfully",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Access counts have been reset to 0"
        }
    except Exception as e:
        logger.error(f"Manual reset failed: {e}")
        raise HTTPException(500, f"Manual reset failed: {e}")

@router.get("/reset-status")
async def get_reset_status():
    """Get current daily-reset status and info."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        data = historical_manager.get_daily_reset_data(today)
        return {
            "daily_reset_active": True,
            "reset_time": "00:00 UTC",
            "current_date": today,
            "has_todays_data": data is not None,
            "data_retention_days": 7,
            "available_dates": historical_manager.get_available_dates(limit=7),
            "description": "Access counts reset to 0 daily at midnight"
        }
    except Exception as e:
        logger.error(f"Failed to get reset status: {e}")
        return {"daily_reset_active": True, "error": str(e)}
