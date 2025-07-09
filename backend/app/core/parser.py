import os
import re
import datetime
from collections import defaultdict

def parse_logs(log_path=None):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    if not log_path:
        log_path = os.getenv("LOG_DIR", "/var/log/sharedlogs")

    if not os.path.exists(log_path):
        print(f"Log path does not exist: {log_path}")
        return {}, {}

    cwd_cache = {}

    # Case 1: Single uploaded file
    if os.path.isfile(log_path):
        log_files = [log_path]
    # Case 2: Folder with multiple .ndjson logs
    elif os.path.isdir(log_path):
        log_files = [
            os.path.join(log_path, f)
            for f in sorted(os.listdir(log_path))
            if f.endswith(".ndjson")
        ]
    else:
        print(f"Invalid log path: {log_path}")
        return {}, {}

    for path in log_files:
        print(f"Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    if 'type=CWD' in line and 'cwd="' in line:
                        event_id = extract_event_id(line)
                        match = re.search(r'cwd="([^"]+)"', line)
                        if match and event_id:
                            cwd_cache[event_id] = match.group(1)

                    elif 'type=PATH' in line and 'name=' in line:
                        event_id = extract_event_id(line)
                        name_match = re.search(r'name="([^"]+)"', line)
                        if not name_match:
                            continue

                        name = name_match.group(1)
                        cwd = cwd_cache.get(event_id, "")
                        full_path = os.path.normpath(os.path.join(cwd, name))

                        TARGET_PREFIX = os.getenv("TARGET_LOG_PREFIX", "/mnt/data")
                        if full_path.startswith(TARGET_PREFIX):
                            access_counts[full_path] += 1
                            timestamp = extract_timestamp(line)
                            if timestamp:
                                access_times[full_path].append(timestamp)
                            good += 1
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    bad += 1

        total_good += good
        total_bad += bad
        print(f"Parsed {good} good entries, Skipped {bad} bad entries.")

    print(f"\nFound {len(access_counts)} unique paths. Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times

def extract_event_id(line):
    match = re.search(r'audit\(\d+\.\d+:(\d+)\)', line)
    return match.group(1) if match else None

def extract_timestamp(line):
    match = re.search(r'audit\((\d+)\.\d+:', line)
    if match:
        try:
            epoch = int(match.group(1))
            dt = datetime.datetime.fromtimestamp(epoch)
            return dt.isoformat()
        except Exception as e:
            print(f"Timestamp parse error: {e}")
            return None
    return None
