import os
import json
from collections import defaultdict

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

    for path in log_files:
        print(f"[INFO] Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    # Extract file path from auditd.data.a0 (first syscall argument)
                    auditd_data = entry.get("auditd", {}).get("data", {})
                    raw_path = auditd_data.get("a0")

                    if raw_path:
                        full_path = os.path.normpath(raw_path)
                        # Optional: filter based on prefix
                        if selected_prefix is None or full_path.startswith(selected_prefix):
                            access_counts[full_path] += 1
                            good += 1

                            if os.getenv("DEBUG_PARSER") == "1":
                                print(f"[DEBUG] Access: {full_path}")

                except json.JSONDecodeError:
                    bad += 1
                    continue

        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")
        total_good += good
        total_bad += bad

    print(f"[RESULT] Total files parsed: {len(log_files)} | Total good: {total_good}, bad: {total_bad}")

    if total_good == 0:
        print("[WARN] No valid file accesses detected.")
        print("       You can debug with: DEBUG_PARSER=1 python3 parser.py")
        print("       Or inspect raw logs manually.")

    return access_counts, access_times

if __name__ == "__main__":
    import sys
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    parse_logs(log_path=path_arg)
