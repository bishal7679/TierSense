import os
import re
import datetime
from collections import defaultdict

def parse_logs(log_path=None, selected_prefix=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    if not log_path:
        log_path = os.getenv("LOG_DIR", "/var/log/sharedlogs")

    if not selected_prefix:
        selected_prefix = os.getenv("TARGET_LOG_PREFIX", "/mnt/data")


    if not os.path.exists(log_path):
        print(f"[ERROR] Log path does not exist: {log_path}")
        return {}, {}

    cwd_cache = {}

    # Identify files
    if os.path.isfile(log_path):
        log_files = [log_path]
    elif os.path.isdir(log_path):
        log_files = [
            os.path.join(log_path, f)
            for f in sorted(os.listdir(log_path))
            if f.endswith(".ndjson")
        ]
    else:
        print(f"[ERROR] Invalid log path: {log_path}")
        return {}, {}

    print(f"[INFO] Using target path prefix: {selected_prefix}")

    for path in log_files:
        print(f"[INFO] Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    # Handle type=CWD to cache working directory per event ID
                    if 'type=CWD' in line and 'cwd="' in line:
                        event_id = extract_event_id(line)
                        cwd_match = re.search(r'cwd="([^"]+)"', line)
                        if cwd_match and event_id:
                            cwd_cache[event_id] = cwd_match.group(1)

                    # Handle type=PATH to resolve full path
                    elif 'type=PATH' in line and 'name=' in line:
                        event_id = extract_event_id(line)
                        name_match = re.search(r'name="([^"]+)"', line)
                        if not name_match or not event_id:
                            continue

                        name = name_match.group(1)
                        cwd = cwd_cache.get(event_id, "")
                        full_path = os.path.normpath(os.path.join(cwd, name))

                        # Only include accesses inside the selected directory
                        if full_path.startswith(selected_prefix):
                            access_counts[full_path] += 1
                            ts = extract_timestamp(line)
                            if ts:
                                access_times[full_path].append(ts)
                            good += 1
                except Exception as e:
                    print(f"[WARN] Error parsing line: {e}")
                    bad += 1

        total_good += good
        total_bad += bad
        print(f"[INFO] File done: {good} valid entries, {bad} skipped.")

    print(f"[RESULT] Total files parsed: {len(access_counts)} | Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times

def extract_event_id(line):
    match = re.search(r'audit\(\d+\.\d+:(\d+)\)', line)
    return match.group(1) if match else None

def extract_timestamp(line):
    match = re.search(r'audit\((\d+)\.\d+:', line)
    if match:
        try:
            epoch = int(match.group(1))
            return datetime.datetime.fromtimestamp(epoch).isoformat()
        except Exception as e:
            print(f"[WARN] Timestamp parse error: {e}")
    return None
