import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List

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

def extract_paths(lines: List[str]) -> List[str]:
    """Return every decoded path string found in PATH, EXE or CWD parts."""
    found: List[str] = []
    for line in lines:
        for regex in FIELD_RES.values():
            for raw in regex.findall(line):
                found.append(decode_escapes(raw))
    return found

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
        buf: Dict[str, List[str]] = defaultdict(list)
        full_path = os.path.join(log_dir, fn)

        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    bad += 1
                    continue

                # optional time filter (based on Filebeat @timestamp)
                if start_ts:
                    ts = iso_to_dt(doc.get("@timestamp", ""))
                    if ts < start_ts:
                        continue

                msg = doc.get("message", "")
                audit_id_match = AUDIT_ID_RE.search(msg)
                if not audit_id_match:
                    continue

                buf[audit_id_match.group(1)].append(msg)

        # process buffered multi-line events
        for event_lines in buf.values():
            for p in extract_paths(event_lines):
                # optional prefix filter
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
        # Pretty-print first 10 entries
        for i, (k, v) in enumerate(result.items()):
            print(f"[DEBUG] {k} → {v}")
            if i == 9:
                break

if __name__ == "__main__":
    _cli()