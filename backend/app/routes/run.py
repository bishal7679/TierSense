from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs, parse_logs_for_date, parse_logs_with_daily_reset
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap, cleanup_old_heatmaps
from app.core.daily_reset import manual_reset  # ← ADD THIS
from app.core.historical import historical_manager  # ← ADD THIS
from app.config import LOG_DIR
import os
import sqlite3
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Add historical data management with daily reset support
HISTORY_DB = os.path.join(LOG_DIR, "tiersense_history.db")

def init_history_db():
    """Initialize historical data database with daily reset tables"""
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
    """Get list of available dates with historical data (daily reset compatible)"""
    try:
        init_history_db()
        with sqlite3.connect(HISTORY_DB) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT date FROM daily_access_counts 
                ORDER BY date DESC LIMIT 30
            """)
            dates = [row[0] for row in cursor.fetchall()]
        
        # Also check for direct NDJSON files (support both date formats)
        if os.path.isdir(LOG_DIR):
            for filename in os.listdir(LOG_DIR):
                if filename.endswith(".ndjson") and "tiersense-processed" in filename:
                    # Extract date from various filename formats
                    if "2025-07-29" in filename and "2025-07-29" not in dates:
                        dates.append("2025-07-29")
                    elif "20250729" in filename and "2025-07-29" not in dates:
                        dates.append("2025-07-29")
        
        return {"available_dates": sorted(list(set(dates)), reverse=True)}
    except Exception as e:
        logger.error(f"Error fetching historical dates: {e}")
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
    """Advanced search for heatmaps with daily reset support"""
    
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
            # Current day analysis with daily reset
            access_counts = parse_logs_with_daily_reset(log_dir=LOG_DIR, prefix=target, debug=False)
            title_suffix = f"Today ({datetime.now().strftime('%Y-%m-%d')}) - Daily Reset"
            
        elif search_type == "date" and date:
            # Single date analysis (independent daily data)
            historical_data = historical_manager.get_daily_reset_data(date)
            if historical_data:
                access_counts = historical_data["access_counts"]
                title_suffix = f"Date: {date} (Daily Reset)"
            else:
                # Fallback to direct log parsing
                access_counts = parse_logs_for_date(LOG_DIR, date, target)
                title_suffix = f"Date: {date}"
            
        elif search_type == "range" and start_date and end_date:
            # Date range analysis - each day independent (no accumulation)
            init_history_db()
            with sqlite3.connect(HISTORY_DB) as conn:
                cursor = conn.execute("""
                    SELECT date, file_path, access_count
                    FROM daily_access_counts 
                    WHERE date BETWEEN ? AND ? AND file_path LIKE ?
                    ORDER BY date DESC, access_count DESC
                """, (start_date, end_date, f"{target}%"))
                
                # Group by date to show daily reset behavior
                daily_data = {}
                for date_str, file_path, count in cursor.fetchall():
                    if date_str not in daily_data:
                        daily_data[date_str] = {}
                    daily_data[date_str][file_path] = count
                
                # For range view, show the most recent day's data
                if daily_data:
                    latest_date = max(daily_data.keys())
                    access_counts = daily_data[latest_date]
                    title_suffix = f"Latest from Range: {latest_date} (Daily Reset)"
                else:
                    access_counts = {}
            
        elif search_type == "pattern":
            # Pattern-based search on current day
            access_counts = parse_logs_with_daily_reset(log_dir=LOG_DIR, prefix=target, debug=False)
            if file_pattern:
                # Filter by pattern
                filtered_counts = {}
                for path, count in access_counts.items():
                    if file_pattern.lower() in path.lower():
                        filtered_counts[path] = count
                access_counts = filtered_counts
                title_suffix = f"Pattern: {file_pattern} (Daily Reset)"
        
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
            "title": title_suffix,
            "daily_reset": True  # Flag indicating daily reset is active
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(500, f"Search failed: {str(e)}")

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    directory: str = Form(None),
    top_n: int = Form(50)
):
    """Enhanced run tiering with daily reset - access counts start fresh each day"""
    
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

    # Parse logs with daily reset (today's counts only)
    today = datetime.now().strftime("%Y-%m-%d")
    access_counts = parse_logs_with_daily_reset(log_dir=LOG_DIR, prefix=target, debug=False)
    
    if not access_counts:
        raise HTTPException(
            400,
            f"No file access events found in today's logs ({today}). "
            "Interact with files under the target directory and try again."
        )

    # Generate heatmap for today's data
    heatmap_path = generate_heatmap(access_counts, top_n=top_n, title_suffix=f"Today ({today}) - Daily Reset")

    # Store today's data with reset logic
    historical_manager.save_daily_reset_data(today, access_counts)
    
    # Clean up old data (keep only last 7 days)
    historical_manager.cleanup_old_reset_data(days_to_keep=7)
    
    # Clean up old heatmaps
    cleanup_old_heatmaps(keep_count=7)

    # Generate LLM analysis on today's fresh counts
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

    # Recompute summary based on today's data
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
        "search_enabled": True,
        "daily_reset": True,  # ← ADD THIS FLAG
        "reset_time": "00:00",  # ← ADD RESET TIME INFO  
        "date": today,
        "message": f"Daily reset: Access counts started fresh for {today}"
    })

# ← ADD THIS: Manual reset endpoint for testing
@router.post("/manual-reset")
async def trigger_manual_reset():
    """Manually trigger daily reset (for testing purposes)"""
    try:
        logger.info("Manual reset triggered via API")
        manual_reset()
        return {
            "status": "success", 
            "message": "Daily reset completed successfully",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Access counts have been reset to 0"
        }
    except Exception as e:
        logger.error(f"Manual reset failed: {e}")
        raise HTTPException(500, f"Manual reset failed: {str(e)}")

# ← ADD THIS: Daily reset status endpoint  
@router.get("/reset-status")
async def get_reset_status():
    """Get daily reset status and information"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if today's data exists
        historical_data = historical_manager.get_daily_reset_data(today)
        has_todays_data = historical_data is not None
        
        # Get available historical dates
        available_dates = historical_manager.get_available_dates(limit=7)
        
        return {
            "daily_reset_active": True,
            "reset_time": "00:00 UTC",
            "current_date": today,
            "has_todays_data": has_todays_data,
            "data_retention_days": 7,
            "available_dates": available_dates,
            "description": "Access counts reset to 0 daily at midnight"
        }
    except Exception as e:
        logger.error(f"Failed to get reset status: {e}")
        return {
            "daily_reset_active": True,
            "error": str(e)
        }
