import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

# Regular expressions parsing
AUDIT_ID_RE = re.compile(r"msg=audit\((\d+\.\d+:\d+)\)")
HEX_RE      = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
FIELD_RES   = {
    "path": re.compile(r'name="([^"]+)"'),
    "exe":  re.compile(r'exe="([^"]+)"'),
    "cwd":  re.compile(r'cwd="([^"]+)"'),
}

def _unhex(match_obj: re.Match) -> str:
    """Convert one or more \\xNN sequences to ASCII."""
    byte_seq = bytes.fromhex(match_obj.group(0).replace("\\x", ""))
    return byte_seq.decode("utf-8", errors="ignore")

def decode_escapes(value: str) -> str:
    """Decode all hex escapes and remove residual backslashes."""
    return HEX_RE.sub(_unhex, value).replace("\\", "")

def iso_to_dt(iso: str) -> datetime:
    """Convert ISO-8601 timestamp to timezone-aware datetime."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))

def parse_logs(
    log_dir: str = "/app/logs",
    prefix: str = "",
    since: str = "",
    debug: bool = False
) -> Dict[str, int]:
    """
    Parse today's tiersense-processed NDJSON audit logs in *log_dir* and
    return a dict mapping each file path to its access count.
    """
    if not os.path.isdir(log_dir):
        print(f"[ERROR] Log directory does not exist: {log_dir}", file=sys.stderr)
        return {}

    # Determine today's date string
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Select only today's NDJSON files
    all_logs = [
        f for f in os.listdir(log_dir)
        if f.endswith(".ndjson")
        and "tiersense-processed" in f
        and today in f
    ]
    if not all_logs:
        print(f"[INFO] No NDJSON logs for {today} in {log_dir}")
        return {}
    # Use only the latest file if multiple match
    latest_log = max(
        all_logs,
        key=lambda fn: os.path.getmtime(os.path.join(log_dir, fn))
    )
    files = [latest_log]
    print(f"[INFO] Processing log: {latest_log}")

    # Optional time filter
    start_ts = iso_to_dt(since) if since else None

    counts: Dict[str, int] = defaultdict(int)

    for fn in files:
        good = bad = 0
        # Buffer per audit event: track cwd and path messages separately
        buf: Dict[str, Dict[str, List[str]]] = defaultdict(
            lambda: {"cwd": [], "path": []}
        )
        full_path = os.path.join(log_dir, fn)

        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue

                # Filter by timestamp if requested
                if start_ts:
                    ts = iso_to_dt(doc.get("@timestamp", ""))
                    if ts < start_ts:
                        continue

                msg = doc.get("message", "")
                m = AUDIT_ID_RE.search(msg)
                if not m:
                    continue
                event_id = m.group(1)

                # Classify message type
                if msg.startswith("type=CWD") or 'cwd="' in msg:
                    buf[event_id]["cwd"].append(msg)
                elif "type=PATH" in msg or 'name="' in msg:
                    buf[event_id]["path"].append(msg)

        # Process each buffered event
        for event in buf.values():
            # Extract the last cwd for this event
            cwd = ""
            for cwd_msg in event["cwd"]:
                m = FIELD_RES["cwd"].search(cwd_msg)
                if m:
                    cwd = decode_escapes(m.group(1))

            # De-duplicate per file within event
            seen: set = set()
            for path_msg in event["path"]:
                m = FIELD_RES["path"].search(path_msg)
                if not m:
                    continue
                raw = decode_escapes(m.group(1))
                # Build absolute path
                p = raw if raw.startswith(os.sep) else os.path.normpath(os.path.join(cwd, raw))
                # Apply prefix filter
                if prefix and not p.startswith(prefix):
                    continue
                # Count each file once per event
                if p in seen:
                    continue
                seen.add(p)
                counts[p] += 1
                good += 1

        print(f"[INFO] {fn}: {good} paths, {bad} malformed JSON lines")

    print(f"[SUMMARY] Unique paths found: {len(counts)}")
    return counts

def _cli():
    ap = argparse.ArgumentParser(description="TierSense NDJSON audit parser")
    ap.add_argument(
        "-d", "--dir",
        default=os.getenv("LOG_DIR", "/app/logs"),
        help="Directory containing Filebeat NDJSON logs"
    )
    ap.add_argument(
        "--prefix", default="",
        help="Only count paths beginning with this prefix"
    )
    ap.add_argument(
        "--since", default="",
        help="ISO timestamp; ignore events before this time"
    )
    ap.add_argument(
        "--debug", action="store_true",
        help="Print decoded paths as they are found"
    )
    args = ap.parse_args()

    result = parse_logs(
        log_dir=args.dir,
        prefix=args.prefix,
        since=args.since,
        debug=args.debug
    )

    if args.debug:
        for i, (k, v) in enumerate(result.items()):
            print(f"[DEBUG] {k} → {v}")
            if i == 9:
                break

if __name__ == "__main__":
    _cli()