# backend/app/core/daily_reset.py
import os
import schedule
import time
import threading
from datetime import datetime
from app.core.historical import historical_manager
from app.config import LOG_DIR
import logging

logger = logging.getLogger(__name__)

def perform_daily_reset():
    """Perform daily reset of access counts"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Performing daily reset for {today}")
        
        # Clean up old log files (keep only today's)
        for filename in os.listdir(LOG_DIR):
            if (filename.endswith(".ndjson") and 
                "tiersense-processed" in filename and 
                today not in filename):
                old_file_path = os.path.join(LOG_DIR, filename)
                os.remove(old_file_path)
                logger.info(f"Removed old log file: {filename}")
        
        # Clean up old historical data (keep only last 7 days)
        historical_manager.cleanup_old_reset_data(days_to_keep=7)
        
        # Clean up old heatmap files
        from app.core.heatmap import cleanup_old_heatmaps
        cleanup_old_heatmaps(keep_count=7)
        
        logger.info(f"Daily reset completed for {today}")
        
    except Exception as e:
        logger.error(f"Daily reset failed: {e}")

def run_daily_reset_scheduler():
    """Run the daily reset scheduler in background thread"""
    logger.info("Starting daily reset scheduler")
    
    # Schedule daily reset at midnight
    schedule.every().day.at("00:00").do(perform_daily_reset)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)

def start_background_scheduler():
    """Start the scheduler in a background thread"""
    scheduler_thread = threading.Thread(target=run_daily_reset_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Daily reset scheduler started in background thread")

# Manual reset function for testing
def manual_reset():
    """Manually trigger a reset (for testing purposes)"""
    logger.info("Manual reset triggered")
    perform_daily_reset()

if __name__ == "__main__":
    run_daily_reset_scheduler()
