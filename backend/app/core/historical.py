# backend/app/core/historical.py
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.config import LOG_DIR
import logging

logger = logging.getLogger(__name__)
HISTORY_DB = os.path.join(LOG_DIR, "tiersense_history.db")

class HistoricalDataManager:
    def __init__(self):
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for daily reset historical data"""
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
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_reset_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    reset_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    files_processed INTEGER NOT NULL,
                    notes TEXT
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_access_counts(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON daily_access_counts(file_path)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reset_date ON daily_reset_log(date)")

    def save_daily_reset_data(self, date: str, access_counts: Dict[str, int]):
        """Save daily access counts with reset logic - each day starts fresh"""
        if not access_counts:
            logger.warning(f"No access counts to save for {date}")
            return
        
        with sqlite3.connect(HISTORY_DB) as conn:
            # Clear any existing data for this date (ensure fresh start)
            conn.execute("DELETE FROM daily_access_counts WHERE date = ?", (date,))
            conn.execute("DELETE FROM daily_summaries WHERE date = ?", (date,))
            
            # Save today's access counts (starting from 0 each day)
            for file_path, count in access_counts.items():
                conn.execute("""
                    INSERT INTO daily_access_counts
                    (date, file_path, access_count) VALUES (?, ?, ?)
                """, (date, file_path, count))
            
            # Calculate and save daily summary
            counts_list = list(access_counts.values())
            if counts_list:  # Only save if we have data
                conn.execute("""
                    INSERT OR REPLACE INTO daily_summaries
                    (date, total_files, max_access_count, min_access_count, avg_access_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    date,
                    len(counts_list),
                    max(counts_list),
                    min(counts_list),
                    sum(counts_list) / len(counts_list)
                ))
            
            # Log the reset operation
            conn.execute("""
                INSERT INTO daily_reset_log
                (date, files_processed, notes) VALUES (?, ?, ?)
            """, (date, len(access_counts), f"Daily reset completed - {len(access_counts)} files processed"))
            
            logger.info(f"Saved daily reset data for {date}: {len(access_counts)} files")

    def get_daily_reset_data(self, date: str) -> Optional[Dict]:
        """Get access counts for a specific date (each day is independent)"""
        with sqlite3.connect(HISTORY_DB) as conn:
            cursor = conn.execute("""
                SELECT file_path, access_count FROM daily_access_counts 
                WHERE date = ? ORDER BY access_count DESC
            """, (date,))
            access_counts = dict(cursor.fetchall())
            
            if access_counts:
                # Get summary for this date
                cursor = conn.execute("""
                    SELECT total_files, max_access_count, min_access_count, avg_access_count
                    FROM daily_summaries WHERE date = ?
                """, (date,))
                summary_row = cursor.fetchone()
                
                return {
                    "date": date,
                    "access_counts": access_counts,
                    "summary": {
                        "total_files": summary_row[0] if summary_row else len(access_counts),
                        "max_access": summary_row[1] if summary_row else (max(access_counts.values()) if access_counts else 0),
                        "min_access": summary_row[2] if summary_row else (min(access_counts.values()) if access_counts else 0),
                        "avg_access": summary_row[3] if summary_row else (sum(access_counts.values()) / len(access_counts) if access_counts else 0)
                    },
                    "daily_reset": True
                }
        return None

    def get_available_dates(self, limit: int = 30) -> List[str]:
        """Get list of available dates with reset data"""
        with sqlite3.connect(HISTORY_DB) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT date FROM daily_access_counts 
                ORDER BY date DESC LIMIT ?
            """, (limit,))
            return [row[0] for row in cursor.fetchall()]

    def cleanup_old_reset_data(self, days_to_keep: int = 7):
        """Clean up old daily reset data (only keep recent days)"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        
        with sqlite3.connect(HISTORY_DB) as conn:
            # Count how much data we're about to remove
            cursor = conn.execute("SELECT COUNT(*) FROM daily_access_counts WHERE date < ?", (cutoff_date,))
            old_count = cursor.fetchone()[0]
            
            # Remove old daily data
            conn.execute("DELETE FROM daily_access_counts WHERE date < ?", (cutoff_date,))
            conn.execute("DELETE FROM daily_summaries WHERE date < ?", (cutoff_date,))
            conn.execute("DELETE FROM daily_reset_log WHERE date < ?", (cutoff_date,))
            
            logger.info(f"Cleaned up {old_count} old records older than {cutoff_date}")

    def get_reset_statistics(self) -> Dict:
        """Get statistics about daily reset operations"""
        with sqlite3.connect(HISTORY_DB) as conn:
            # Get total days with data
            cursor = conn.execute("SELECT COUNT(DISTINCT date) FROM daily_access_counts")
            total_days = cursor.fetchone()[0]
            
            # Get recent reset operations
            cursor = conn.execute("""
                SELECT date, files_processed, reset_timestamp 
                FROM daily_reset_log 
                ORDER BY date DESC LIMIT 7
            """)
            recent_resets = cursor.fetchall()
            
            # Get average files per day
            cursor = conn.execute("""
                SELECT AVG(total_files) FROM daily_summaries
            """)
            avg_files_per_day = cursor.fetchone()[0] or 0
            
            return {
                "total_days_tracked": total_days,
                "recent_resets": [
                    {"date": r[0], "files_processed": r[1], "timestamp": r[2]} 
                    for r in recent_resets
                ],
                "avg_files_per_day": round(avg_files_per_day, 2),
                "retention_days": 7
            }

    def compare_daily_data(self, date1: str, date2: str) -> Dict:
        """Compare data between two dates (useful for daily reset analysis)"""
        data1 = self.get_daily_reset_data(date1)
        data2 = self.get_daily_reset_data(date2)
        
        if not data1 or not data2:
            return {"error": "One or both dates have no data"}
        
        return {
            "date1": date1,
            "date2": date2,
            "date1_files": data1["summary"]["total_files"],
            "date2_files": data2["summary"]["total_files"],
            "date1_max_access": data1["summary"]["max_access"],
            "date2_max_access": data2["summary"]["max_access"],
            "common_files": len(set(data1["access_counts"].keys()) & set(data2["access_counts"].keys())),
            "daily_reset_note": "Each day starts with 0 access counts - no accumulation across dates"
        }

    def export_daily_data(self, date: str, format: str = "json") -> str:
        """Export daily data in specified format"""
        data = self.get_daily_reset_data(date)
        if not data:
            return None
        
        if format.lower() == "json":
            return json.dumps(data, indent=2)
        elif format.lower() == "csv":
            lines = ["file_path,access_count"]
            for path, count in data["access_counts"].items():
                lines.append(f'"{path}",{count}')
            return "\n".join(lines)
        
        return None

# Global instance
historical_manager = HistoricalDataManager()