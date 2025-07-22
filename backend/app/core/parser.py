import os
import re
import json
from collections import defaultdict

def parse_logs(log_path=None, selected_prefix=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list) # Kept for consistent function signature, though not used in this version.
    total_good, total_bad = 0, 0

    # This logic correctly finds the log directory.
    log_path = log_path or os.getenv("LOG_DIR", "/app/logs")
    
    if not os.path.exists(log_path):
        print(f"[ERROR] Log path does not exist: {log_path}")
        return {}, {}

    # This logic correctly handles finding all .ndjson files in the directory.
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
                # --- START OF CORRECTED LOGIC ---
                try:
                    # Each line from Filebeat is a JSON object.
                    log_entry = json.loads(line)
                    message = log_entry.get("message", "")

                    # We only care about logs that contain our specific monitoring key.
                    if 'key="tiersense_monitoring"' not in message:
                        continue # Skip lines that are not relevant to our monitoring.

                    # Extract the full, absolute path of the file that was accessed.
                    path_match = re.search(r'name="([^"]+)"', message)
                    
                    if path_match:
                        full_path = os.path.normpath(path_match.group(1))
                        
                        # A simple check to ensure we are counting files, not directories.
                        if '.' in os.path.basename(full_path) or not full_path.endswith('/'):
                            access_counts[full_path] += 1
                            good += 1

                except (json.JSONDecodeError, AttributeError):
                    # This will safely ignore any lines that are not valid JSON.
                    bad += 1
                    continue
                # --- END OF CORRECTED LOGIC ---

        total_good += good
        total_bad += bad
        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")

    print(f"[RESULT] Total files parsed: {len(log_files)} | Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times
