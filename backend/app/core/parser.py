import os
import re
from collections import defaultdict

def parse_logs(log_dir=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    if not log_dir:
        log_dir = os.getenv("LOG_DIR", "/var/log/sharedlogs")

    if not os.path.exists(log_dir):
        print(f"Log directory does not exist: {log_dir}")
        return {}, {}

    last_known_cwd = ""  # Track most recent cwd globally

    for filename in sorted(os.listdir(log_dir)):
        if not filename.endswith(".ndjson"):
            continue

        path = os.path.join(log_dir, filename)
        print(f"Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    # Extract CWD from "type=CWD"
                    if 'type=CWD' in line and 'cwd="' in line:
                        match = re.search(r'cwd="([^"]+)"', line)
                        if match:
                            last_known_cwd = match.group(1)

                    # Extract file path from "type=PATH"
                    elif 'type=PATH' in line and 'name=' in line:
                        name_match = re.search(r'name="([^"]+)"', line)
                        if not name_match:
                            continue

                        name = name_match.group(1)
                        full_path = os.path.normpath(os.path.join(last_known_cwd, name))

                        if full_path.startswith("/mnt/data"):
                            access_counts[full_path] += 1
                            access_times[full_path].append("")  # Placeholder if you want timestamps later
                            good += 1
                    # If not CWD or PATH, ignore (don’t count as bad)
                except Exception as e:
                    print(f"❌ Error parsing line: {e}")
                    bad += 1

        total_good += good
        total_bad += bad
        print(f"Parsed {good} good entries, Skipped {bad} bad entries.")

    print(f"\nFound {len(access_counts)} unique paths. Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times
