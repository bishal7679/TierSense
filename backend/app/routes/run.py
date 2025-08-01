# backend/app/routes/run.py

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs_for_date, parse_logs_with_daily_reset
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap, cleanup_old_heatmaps
from app.core.daily_reset import manual_reset
from app.core.historical import historical_manager
from app.config import LOG_DIR, HEATMAP_PATH, load_tier_ranges
import os
import sqlite3
import re
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


def extract_date_from_filename(filename: str) -> str:
    """
    Extract date dynamically from filename (supports YYYY-MM-DD and YYYYMMDD).
    """
    date_pattern_hyphen = re.compile(r'(\d{4}-\d{2}-\d{2})')
    date_pattern_compact = re.compile(r'(\d{8})')
    match = date_pattern_hyphen.search(filename)
    if match:
        return match.group(1)
    match = date_pattern_compact.search(filename)
    if match:
        ds = match.group(1)
        return f"{ds[:4]}-{ds[4:6]}-{ds[6:8]}"
    return None


def calculate_tier_counts(counts):
    """
    Calculate HOT/WARM/COLD counts using dynamic ranges.
    """
    ranges = load_tier_ranges()
    hot_min, hot_max = ranges["HOT"]
    warm_min, warm_max = ranges["WARM"]
    cold_min, cold_max = ranges["COLD"]

    hot = warm = cold = 0
    for c in counts:
        if (hot_min is None or c >= hot_min) and (hot_max is None or c <= hot_max):
            hot += 1
        elif (warm_min is None or c >= warm_min) and (warm_max is None or c <= warm_max):
            warm += 1
        elif (cold_max is None or c <= cold_max):
            cold += 1
        else:
            # values outside defined tiers count as COLD by default
            cold += 1
    return hot, warm, cold


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
        dates = [r[0] for r in rows]
        if os.path.isdir(LOG_DIR):
            for fn in os.listdir(LOG_DIR):
                if fn.startswith("tiersense-processed") and fn.endswith(".ndjson"):
                    d = extract_date_from_filename(fn)
                    if d and d not in dates:
                        dates.append(d)
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
        # Purge old heatmaps
        hm_dir = os.path.dirname(HEATMAP_PATH)
        if os.path.isdir(hm_dir):
            for f in os.listdir(hm_dir):
                if f.startswith("access_heatmap_") and f.endswith(".png"):
                    try: os.remove(os.path.join(hm_dir, f))
                    except: pass

        if search_type == "current":
            access_counts = parse_logs_with_daily_reset(LOG_DIR, prefix=target, debug=False)
            title = f"Today ({datetime.now():%Y-%m-%d}) - Daily Reset"
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
                access_counts = {p: c for p, c in access_counts.items() if file_pattern.lower() in p.lower()}
            title = f"Pattern: {file_pattern} (Daily Reset)"
        else:
            raise HTTPException(400, "Invalid search type or missing parameters")

        if not access_counts:
            raise HTTPException(404, "No data found for the specified search criteria")

        total_files = len(access_counts)
        hot_tier, warm_tier, cold_tier = calculate_tier_counts(access_counts.values())

        top_items = dict(sorted(access_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
        heatmap_url = generate_heatmap(top_items, top_n, title)

        return {
            "heatmap": heatmap_url,
            "search_type": search_type,
            "total_files": total_files,
            "displayed_files": len(top_items),
            "top_n": top_n,
            "title": title,
            "daily_reset": True,
            "summary": {
                "total_files": total_files,
                "hot_tier": hot_tier,
                "warm_tier": warm_tier,
                "cold_tier": cold_tier
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search heatmaps failed: {e}")
        raise HTTPException(500, f"Search heatmaps failed: {e}")


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

    # Purge old heatmaps
    hm_dir = os.path.dirname(HEATMAP_PATH)
    if os.path.isdir(hm_dir):
        for f in os.listdir(hm_dir):
            if f.startswith("access_heatmap_") and f.endswith(".png"):
                try: os.remove(os.path.join(hm_dir, f))
                except: pass

    today = datetime.now().strftime("%Y-%m-%d")
    access_counts = parse_logs_with_daily_reset(LOG_DIR, prefix=target, debug=False)
    if not access_counts:
        raise HTTPException(400, f"No file access events found for {today}")

    # Generate heatmap
    heatmap_url = generate_heatmap(access_counts, top_n=top_n, title_suffix=f"Today ({today}) - Daily Reset")

    # Persist historical data
    historical_manager.save_daily_reset_data(today, access_counts)
    historical_manager.cleanup_old_reset_data(days_to_keep=7)
    cleanup_old_heatmaps(keep_count=1)

    # LLM tiering suggestions
    suggestions = generate_tiering_suggestions(llm, access_counts, api_key)

    # Calculate dynamic summary
    total_files = len(access_counts)
    hot_tier, warm_tier, cold_tier = calculate_tier_counts(access_counts.values())

    # Post-process analysis paths
    def strip_pref(p: str) -> str:
        return p.replace("/host-root", "", 1) if p.startswith("/host-root") else p

    analysis = []
    for ent in suggestions.get("analysis", []):
        path = strip_pref(ent["path"])
        if path == target or not os.path.exists(path) or os.path.isdir(path):
            continue
        ent["path"] = path
        analysis.append(ent)

    summary = {
        "total_files": total_files,
        "hot_tier": hot_tier,
        "warm_tier": warm_tier,
        "cold_tier": cold_tier
    }

    return JSONResponse({
        "heatmap": heatmap_url,
        "analysis": analysis,
        "summary": summary,
        "top_n_displayed": min(top_n, total_files),
        "daily_reset": True,
        "reset_time": "00:00",
        "date": today,
        "message": f"Daily reset completed for {today}"
    })


@router.post("/manual-reset")
async def trigger_manual_reset():
    """Manually trigger daily reset for testing."""
    try:
        logger.info("Manual reset triggered")
        # Purge heatmaps
        hm_dir = os.path.dirname(HEATMAP_PATH)
        if os.path.isdir(hm_dir):
            for f in os.listdir(hm_dir):
                if f.startswith("access_heatmap_") and f.endswith(".png"):
                    try: os.remove(os.path.join(hm_dir, f))
                    except: pass
        manual_reset()
        return {
            "status": "success",
            "message": "Manual daily reset completed",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            "description": "Access counts reset daily at midnight"
        }
    except Exception as e:
        logger.error(f"Reset status failed: {e}")
        return {"daily_reset_active": True, "error": str(e)}
