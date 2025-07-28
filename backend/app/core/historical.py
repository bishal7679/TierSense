# backend/app/core/historical.py
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.config import LOG_DIR

HISTORY_DB = os.path.join(LOG_DIR, "tiersense_history.db")

class HistoricalDataManager:
    def __init__(self):
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for historical data"""
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
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    heatmap_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)
            
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_access_counts(date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON daily_access_counts(file_path)")
    
    def save_daily_data(self, date: str, access_counts: Dict[str, int], analysis_data: dict, heatmap_path: str):
        """Save daily access counts and analysis results"""
        with sqlite3.connect(HISTORY_DB) as conn:
            # Save access counts
            for file_path, count in access_counts.items():
                conn.execute("""
                    INSERT OR REPLACE INTO daily_access_counts 
                    (date, file_path, access_count) VALUES (?, ?, ?)
                """, (date, file_path, count))
            
            # Save analysis results
            conn.execute("""
                INSERT OR REPLACE INTO analysis_results 
                (date, analysis_data, heatmap_path) VALUES (?, ?, ?)
            """, (date, json.dumps(analysis_data), heatmap_path))
    
    def get_daily_data(self, date: str) -> Optional[Dict]:
        """Retrieve data for a specific date"""
        with sqlite3.connect(HISTORY_DB) as conn:
            # Get access counts
            cursor = conn.execute("""
                SELECT file_path, access_count FROM daily_access_counts 
                WHERE date = ? ORDER BY access_count DESC
            """, (date,))
            access_counts = dict(cursor.fetchall())
            
            # Get analysis data
            cursor = conn.execute("""
                SELECT analysis_data, heatmap_path FROM analysis_results WHERE date = ?
            """, (date,))
            result = cursor.fetchone()
            
            if result:
                analysis_data, heatmap_path = result
                return {
                    "access_counts": access_counts,
                    "analysis": json.loads(analysis_data),
                    "heatmap_path": heatmap_path
                }
        return None
    
    def get_available_dates(self, limit: int = 30) -> List[str]:
        """Get list of available dates with data"""
        with sqlite3.connect(HISTORY_DB) as conn:
            cursor = conn.execute("""
                SELECT DISTINCT date FROM daily_access_counts 
                ORDER BY date DESC LIMIT ?
            """, (limit,))
            return [row[0] for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Remove data older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
        
        with sqlite3.connect(HISTORY_DB) as conn:
            # Clean database
            conn.execute("DELETE FROM daily_access_counts WHERE date < ?", (cutoff_date,))
            conn.execute("DELETE FROM analysis_results WHERE date < ?", (cutoff_date,))
            
            # Clean old heatmap files
            heatmap_dir = os.path.dirname(HEATMAP_PATH)
            if os.path.exists(heatmap_dir):
                for filename in os.listdir(heatmap_dir):
                    if filename.startswith("access_heatmap_") and filename.endswith(".png"):
                        file_path = os.path.join(heatmap_dir, filename)
                        file_time = os.path.getctime(file_path)
                        if datetime.fromtimestamp(file_time) < datetime.now() - timedelta(days=days_to_keep):
                            os.remove(file_path)

# Global instance
historical_manager = HistoricalDataManager()
