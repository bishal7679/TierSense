import os
import sys
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

AUDIT_ID_RE = re.compile(r"msg=audit\((\d+\.\d+:\d+)\)")
HEX_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
FIELD_RES = {
    "path": re.compile(r'name="([^"]+)"'),
    "cwd": re.compile(r'cwd="([^"]+)"'),
}

def _unhex(match_obj):
    return bytes.fromhex(match_obj.group(0).replace("\\x", "")).decode("utf-8", errors="ignore")

def decode_escapes(val: str) -> str:
    return HEX_RE.sub(_unhex, val).replace("\\", "")

def iso_to_dt(iso: str):
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))

def parse_logs(
    log_dir: str = "/app/logs",
    prefix: str = "",
    since: str = "",
    debug: bool = False
) -> Dict[str, int]:
    if not os.path.isdir(log_dir):
        print(f"[ERROR] Log directory does not exist: {log_dir}", file=sys.stderr)
        return {}

    # Try to match today's date in both formats (2025-07-28 and 20250728)
    today1 = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today2 = datetime.now(timezone.utc).strftime("%Y%m%d")
    all_logs = [
        f for f in os.listdir(log_dir)
        if f.endswith(".ndjson")
        and "tiersense-processed" in f
        and (today1 in f or today2 in f)
    ]
    if not all_logs:
        print(f"[INFO] No NDJSON logs for {today1}/{today2} in {log_dir}")
        return {}

    latest_log = max(all_logs, key=lambda fn: os.path.getmtime(os.path.join(log_dir, fn)))
    files = [latest_log]
    print(f"[INFO] Processing log: {latest_log}")

    start_ts = iso_to_dt(since) if since else None
    counts = defaultdict(int)

    for fn in files:
        good = bad = 0
        buf = defaultdict(lambda: {"cwd": [], "path": []})
        full_path = os.path.join(log_dir, fn)
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue
                if start_ts:
                    ts = iso_to_dt(doc.get("@timestamp", ""))
                    if ts < start_ts:
                        continue
                msg = doc.get("message", "")
                m = AUDIT_ID_RE.search(msg)
                if not m:
                    continue
                event_id = m.group(1)
                if msg.startswith("type=CWD") or 'cwd="' in msg:
                    buf[event_id]["cwd"].append(msg)
                elif "type=PATH" in msg or 'name="' in msg:
                    buf[event_id]["path"].append(msg)
        for event in buf.values():
            cwd = ""
            for cwd_msg in event["cwd"]:
                m = FIELD_RES["cwd"].search(cwd_msg)
                if m:
                    cwd = decode_escapes(m.group(1))
            seen = set()
            for path_msg in event["path"]:
                m = FIELD_RES["path"].search(path_msg)
                if not m:
                    continue
                raw = decode_escapes(m.group(1))
                p = raw if raw.startswith(os.sep) else os.path.normpath(os.path.join(cwd, raw))
                if prefix and not p.startswith(prefix):
                    continue
                if p in seen:
                    continue
                seen.add(p)
                counts[p] += 1
                good += 1
        print(f"[INFO] {fn}: {good} paths, {bad} malformed JSON lines")

    print(f"[SUMMARY] Unique paths found: {len(counts)}")
    return counts