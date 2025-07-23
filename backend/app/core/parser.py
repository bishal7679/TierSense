import os
import re
import json
from collections import defaultdict

def parse_logs(log_path=None, selected_prefix=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)  # Kept for consistency if you plan to use it later.
    total_good, total_bad = 0, 0

    # Default to environment variable LOG_DIR or /app/logs if not provided
    log_path = log_path or os.getenv("LOG_DIR", "/app/logs")
    
    if not os.path.exists(log_path):
        print(f"[ERROR] Log path does not exist: {log_path}")
        return {}, {}

    # Get log files based on whether log_path is a file or directory
    if os.path.isfile(log_path):
        log_files = [log_path]
    elif os.path.isdir(log_path):
        log_files = sorted([
            os.path.join(log_path, f)
            for f in os.listdir(log_path)
            if f.endswith(".ndjson") and "tiersense-processed" in f
        ])
    else:
        print(f"[ERROR] Invalid log path: {log_path}")
        return {}, {}

    print(f"[INFO] Found {len(log_files)} log files to parse.")

    for path in log_files:
        print(f"[INFO] Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    # Parse JSON entry
                    log_entry = json.loads(line)
                    message = log_entry.get("message", "")

                    # Match logs with the specific monitoring key
                    if not re.search(r'key\s*=?\s*"?tiersense_monitoring"?', message):
                        continue  # Skip irrelevant logs

                    # Extract file paths and filter based on criteria
                    path_matches = re.findall(r'name="([^"]+)"', message)
                    for p in path_matches:
                        full_path = os.path.normpath(p)
                        
                        # Only count files with extensions or directories
                        if '.' in os.path.basename(full_path) or not full_path.endswith('/'):
                            access_counts[full_path] += 1
                            good += 1

                except (json.JSONDecodeError, AttributeError) as e:
                    # Log error for debugging skipped entries
                    print(f"[ERROR] Skipped line due to error: {e}")
                    bad += 1
                    continue

        total_good += good
        total_bad += bad
        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")

    print(f"[RESULT] Total files parsed: {len(log_files)} | Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times