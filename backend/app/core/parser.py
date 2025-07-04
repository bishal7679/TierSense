import os 
import json
import re
from collections import defaultdict

def parse_logs(log_dir=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    if not log_dir:
        log_dir = os.getenv("LOG_DIR", "/mnt/nfs-logs")

    if not os.path.exists(log_dir):
        print(f"❌ Log directory does not exist: {log_dir}")
        return {}, {}

    cwd_cache = {}

    for filename in sorted(os.listdir(log_dir)):
        if not filename.endswith(".ndjson"):
            continue

        path = os.path.join(log_dir, filename)
        print(f"📄 Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    if "type=CWD" in line and 'cwd="' in line:
                        match = re.search(r'cwd="([^"]+)"', line)
                        if match:
                            event_id = extract_event_id(line)
                            cwd_cache[event_id] = match.group(1)

                    if "type=PATH" in line and 'name=' in line:
                        event_id = extract_event_id(line)
                        cwd = cwd_cache.get(event_id, "")
                        name_match = re.search(r'name="([^"]+)"', line)
                        if not name_match:
                            continue
                        name = name_match.group(1)

                        full_path = os.path.join(cwd, name)
                        if full_path.startswith("/"):
                            access_counts[full_path] += 1
                            access_times[full_path].append("")
                            good += 1
                    else:
                        bad += 1

                except Exception as e:
                    print(f"❌ Error: {e}")
                    bad += 1

        total_good += good
        total_bad += bad
        print(f"✅ Parsed {good} good entries, ⚠️ Skipped {bad} bad entries.")

    print(f"\n📊 Found {len(access_counts)} unique paths. Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times

def extract_event_id(line):
    match = re.search(r'audit\(\d+\.\d+:(\d+)\)', line)
    return match.group(1) if match else None
