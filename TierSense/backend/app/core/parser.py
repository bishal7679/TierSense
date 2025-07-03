import os
import json
import re
from collections import defaultdict

# Regex to extract relevant file paths under /mnt/data
DATA_PATH_PATTERN = re.compile(r'name=(?:\\?"|")?(/mnt/data/[^"\\\s]+)')

def parse_logs(log_dir):
    access_counts = defaultdict(int)
    access_times = defaultdict(list)
    total_good, total_bad = 0, 0

    if not os.path.exists(log_dir):
        print(f"❌ Log directory does not exist: {log_dir}")
        return {}, {}

    for filename in sorted(os.listdir(log_dir)):
        if not filename.endswith(".ndjson"):
            continue

        path = os.path.join(log_dir, filename)
        print(f"📄 Processing file: {path}")
        good, bad = 0, 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    msg = data.get("message", "")
                    if "/mnt/data" not in msg:
                        continue

                    matches = DATA_PATH_PATTERN.findall(msg)
                    for match in matches:
                        access_counts[match] += 1
                        access_times[match].append(data.get("@timestamp", ""))
                    if matches:
                        good += 1
                except Exception:
                    bad += 1

        total_good += good
        total_bad += bad
        print(f"✅ Parsed {good} good entries, ⚠️ Skipped {bad} bad entries.")

    print(f"\n📊 Found {len(access_counts)} unique paths. Total good: {total_good}, bad: {total_bad}")
    return access_counts, access_times
