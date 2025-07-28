import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

AUDIT_ID_RE =re.compile(r"msg=audit\((\d+\.\d+:\d+)\)")
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
    Parse every tiersense-processed*.ndjson file in *log_dir* and
    return a dict {filepath: access_count}.
    """
    if not os.path.isdir(log_dir):
        print(f"[ERROR] path does not exist or is not a directory: {log_dir}", file=sys.stderr)
        return {}

    files = sorted(
        f for f in os.listdir(log_dir)
        if f.endswith(".ndjson") and "tiersense-processed" in f
    )
    print(f"[INFO] NDJSON files detected: {len(files)}")

    start_ts = iso_to_dt(since) if since else None
    counts: Dict[str, int] = defaultdict(int)

    for fn in files:
        good = bad = 0
        # buffer audit messages per event id, capturing cwd and path messages
        buf: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: {"cwd": [], "path": []})
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

                # classify message type
                if msg.startswith("type=CWD") or 'cwd="' in msg:
                    buf[event_id]["cwd"].append(msg)
                elif "type=PATH" in msg or 'name="' in msg:
                    buf[event_id]["path"].append(msg)

        # process each event: reconstruct full paths
        for event in buf.values():
            # extract last cwd for this event
            cwd = ""
            for cwd_msg in event["cwd"]:
                m = FIELD_RES["cwd"].search(cwd_msg)
                if m:
                    cwd = decode_escapes(m.group(1))

            # extract each path, prefixing relative names with cwd
            for path_msg in event["path"]:
                m = FIELD_RES["path"].search(path_msg)
                if not m:
                    continue
                raw = decode_escapes(m.group(1))
                p = raw if raw.startswith(os.sep) else os.path.normpath(os.path.join(cwd, raw))

                if prefix and not p.startswith(prefix):
                    continue

                counts[p] += 1
                good += 1

        print(f"[INFO] {fn}: {good} paths, {bad} malformed JSON lines")

    print(f"[SUMMARY] Unique paths found: {len(counts)}")
    return counts

def _cli():
    ap = argparse.ArgumentParser(description="TierSense NDJSON audit parser")
    ap.add_argument("-d", "--dir", default=os.getenv("LOG_DIR", "/app/logs"),
                    help="Directory containing Filebeat NDJSON logs")
    ap.add_argument("--prefix", default="",
                    help="Only count paths beginning with this prefix")
    ap.add_argument("--since", default="",
                    help="ISO timestamp; ignore events before this time")
    ap.add_argument("--debug", action="store_true",
                    help="Print decoded paths as they are found")
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
