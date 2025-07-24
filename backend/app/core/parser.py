import os
import re
import json
from collections import defaultdict

AUDIT_KEY = "tiersense_monitoring"

def parse_logs(log_path=None, selected_prefix=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    log_path = log_path or os.getenv("LOG_DIR", "/app/logs")

    if not os.path.exists(log_path):
        print(f"[ERROR] Log path does not exist: {log_path}")
        return {}, {}

    log_files = [log_path] if os.path.isfile(log_path) else sorted([
        os.path.join(log_path, f)
        for f in os.listdir(log_path)
        if f.endswith(".ndjson") and "tiersense-processed" in f
    ])

    print(f"[INFO] Found {len(log_files)} log files to parse.")

    event_buffer = defaultdict(list)

    for path in log_files:
        print(f"[INFO] Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    message = entry.get("message", "")
                    
                    # Extract audit ID like msg=audit(1234:567)
                    match = re.search(r'msg=audit\((\d+:\d+)\)', message)
                    if not match:
                        continue

                    audit_id = match.group(1)
                    event_buffer[audit_id].append(message)

                except json.JSONDecodeError:
                    bad += 1
                    continue

        # Process buffered events
        for event_lines in event_buffer.values():
            # Check if any line contains the tiersense_monitoring key
            if not any(re.search(r'key\s*=\s*"?tiersense_monitoring"?', line) for line in event_lines):
                continue

            paths = []
            for line in event_lines:
                path_matches = re.findall(r'name="((?:\\.|[^"\\])*)"', line)
                paths.extend(path_matches)

            if os.getenv("DEBUG_PARSER") == "1":
                print(f"[DEBUG] Matched paths: {paths}")

            for p in paths:
                full_path = os.path.normpath(p)
                if full_path:
                    access_counts[full_path] += 1
                    good += 1

        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")
        total_good += good
        total_bad += bad
        event_buffer.clear()

    print(f"[RESULT] Total files parsed: {len(log_files)} | Total good: {total_good}, bad: {total_bad}")

    if total_good == 0:
        print("[WARN] No valid audit entries found with 'tiersense_monitoring'.")
        print("       You can debug with: DEBUG_PARSER=1 python3 parser.py")
        print("       Or run: sudo ausearch -k tiersense_monitoring")

    return access_counts, access_times

if __name__ == "__main__":
    import sys
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    parse_logs(log_path=path_arg)