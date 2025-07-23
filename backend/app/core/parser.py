import os
import re
import json
from collections import defaultdict

def parse_logs(log_path=None, selected_prefix=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)  # Reserved for future use
    total_good, total_bad = 0, 0

    # Use provided path or environment fallback
    log_path = log_path or os.getenv("LOG_DIR", "/app/logs")

    if not os.path.exists(log_path):
        print(f"[ERROR] Log path does not exist: {log_path}")
        return {}, {}

    # Detect log files
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
                    log_entry = json.loads(line)
                    message = log_entry.get("message", "")

                    # Filter logs by audit key
                    if not re.search(r'key\s*=?\s*"?tiersense_monitoring"?', message):
                        if os.getenv("DEBUG_PARSER") == "1":
                            print("[DEBUG] Skipping log, no tiersense_monitoring key:", message[:200])
                        continue

                    # Extract paths using safe regex (handles escaped quotes)
                    path_matches = re.findall(r'name="((?:\\.|[^"\\])*)"', message)
                    if os.getenv("DEBUG_PARSER") == "1":
                        print(f"[DEBUG] Matched paths: {path_matches}")

                    for p in path_matches:
                        full_path = os.path.normpath(p)

                        # Count only files or leaf paths (not trailing '/')
                        if '.' in os.path.basename(full_path) or not full_path.endswith('/'):
                            access_counts[full_path] += 1
                            good += 1

                except (json.JSONDecodeError, AttributeError) as e:
                    bad += 1
                    if os.getenv("DEBUG_PARSER") == "1":
                        print(f"[ERROR] Skipped line due to error: {e}")
                    continue

        total_good += good
        total_bad += bad
        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")

    print(f"[RESULT] Total files parsed: {len(log_files)} | Total good: {total_good}, bad: {total_bad}")

    if total_good == 0:
        print("[WARN] No valid audit entries found with 'tiersense_monitoring'.")
        print("       You can debug with: DEBUG_PARSER=1 python3 parser.py")
        print("       Or run: sudo ausearch -k tiersense_monitoring")

    return access_counts, access_times

# Optional direct run
if __name__ == "__main__":
    import sys
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    parse_logs(log_path=path_arg)
