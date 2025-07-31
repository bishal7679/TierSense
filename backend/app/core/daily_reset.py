# backend/app/core/daily_reset.py

import os
import schedule
import time
import threading
import subprocess
from datetime import datetime
from app.core.historical import historical_manager
from app.config import LOG_DIR
import logging

logger = logging.getLogger(__name__)

def perform_daily_reset():
    """Perform daily reset of access counts with complete file cleanup and Filebeat restart"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        logger.info(f"Performing daily reset for {today}")
        
        # Step 1: Stop Filebeat to release file handles
        try:
            subprocess.run(['pkill', '-f', 'filebeat'], check=False, capture_output=True)
            time.sleep(2)  # Give Filebeat time to stop
            logger.info("Stopped Filebeat for daily reset")
        except Exception as e:
            logger.warning(f"Failed to stop Filebeat: {e}")
        
        # Step 2: Clean up ALL NDJSON files (including today's) to force fresh start
        removed_files = []
        for filename in os.listdir(LOG_DIR):
            if filename.endswith(".ndjson") and "tiersense-processed" in filename:
                full_path = os.path.join(LOG_DIR, filename)
                try:
                    os.remove(full_path)
                    removed_files.append(filename)
                    logger.info(f"Removed log file during reset: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to remove {filename}: {e}")
        
        # Step 3: Clean up old historical data (keep only last 7 days)
        historical_manager.cleanup_old_reset_data(days_to_keep=7)
        
        # Step 4: Clean up old heatmap files
        from app.core.heatmap import cleanup_old_heatmaps
        cleanup_old_heatmaps(keep_count=7)
        
        # Step 5: Restart Filebeat to create fresh file for today
        try:
            with open('/app/logs/filebeat.log', 'a') as log_file:
                subprocess.Popen(
                    ['nohup', 'filebeat', '-e', '-c', '/etc/filebeat/filebeat.yml'],
                    stdout=log_file, stderr=subprocess.STDOUT,
                    preexec_fn=os.setsid
                )
            time.sleep(3)  # Give Filebeat time to start
            logger.info("Restarted Filebeat for fresh file creation")
        except Exception as e:
            logger.error(f"Failed to restart Filebeat: {e}")
        
        logger.info(f"Daily reset completed for {today} - removed {len(removed_files)} files")
    except Exception as e:
        logger.error(f"Daily reset failed: {e}")

def run_daily_reset_scheduler():
    """Run the daily reset scheduler in background thread"""
    logger.info("Starting daily reset scheduler")
    schedule.every().day.at("00:00").do(perform_daily_reset)
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)

def start_background_scheduler():
    """Start the scheduler in a background thread"""
    thread = threading.Thread(target=run_daily_reset_scheduler, daemon=True)
    thread.start()
    logger.info("Daily reset scheduler started in background thread")

def manual_reset():
    """Manually trigger a reset (for testing purposes)"""
    logger.info("Manual reset triggered")
    perform_daily_reset()
    time.sleep(5)  # Allow Filebeat to stabilize
    try:
        result = subprocess.run(['pgrep', '-f', 'filebeat'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Manual reset completed - Filebeat is running")
        else:
            logger.warning("Manual reset completed but Filebeat may not be running")
    except Exception as e:
        logger.warning(f"Could not verify Filebeat status: {e}")

def get_reset_status():
    """Get current reset status information"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        ndjson_files = [
            f for f in os.listdir(LOG_DIR)
            if f.endswith('.ndjson') and 'tiersense-processed' in f
        ]
        try:
            proc = subprocess.run(['pgrep', '-f', 'filebeat'], capture_output=True)
            filebeat_running = (proc.returncode == 0)
        except:
            filebeat_running = False
        return {
            "daily_reset_active": True,
            "reset_time": "00:00 UTC",
            "current_date": today,
            "ndjson_files": ndjson_files,
            "filebeat_running": filebeat_running,
            "data_retention_days": 7
        }
    except Exception as e:
        logger.error(f"Failed to get reset status: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    run_daily_reset_scheduler()
