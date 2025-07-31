import os
import sys
import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Tuple


# Regex patterns for parsing audit messages
AUDIT_ID_RE = re.compile(r"msg=audit\((\d+\.\d+:\d+)\)")
HEX_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
FIELD_RES = {
    "path": re.compile(r'name="([^"]+)"'),
    "cwd":  re.compile(r'cwd="([^"]+)"'),
}


def _unhex(match_obj) -> str:
    """Convert hex-encoded bytes to UTF-8 string."""
    try:
        byte_seq = bytes.fromhex(match_obj.group(0).replace("\\x", ""))
        return byte_seq.decode("utf-8", errors="ignore")
    except ValueError:
        return match_obj.group(0)


def decode_escapes(val: str) -> str:
    """Decode hex escapes and remove backslashes."""
    if not val:
        return ""
    return HEX_RE.sub(_unhex, val).replace("\\", "")


def iso_to_dt(iso: str) -> Optional[datetime]:
    """Convert ISO-8601 timestamp to timezone-aware datetime."""
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_log_files(log_dir: str, target_date: Optional[str] = None) -> List[str]:
    """
    Find NDJSON log files handling Filebeat's actual output patterns.
    Handles multiple naming formats that Filebeat creates:
    - tiersense-processed-YYYY-MM-DD.ndjson (expected format)
    - tiersense-processed-YYYYMMDD.ndjson (compact format)
    - tiersense-processed-YYYYMMDD-1.ndjson (rotated files)
    - tiersense-processed-YYYY-MM-DD-1.ndjson (rotated with hyphens)
    """
    date_hyphen = target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_compact = date_hyphen.replace("-", "")  # YYYYMMDD format
    
    candidates = []
    
    for filename in os.listdir(log_dir):
        if not (filename.startswith("tiersense-processed") and filename.endswith(".ndjson")):
            continue
            
        # Priority 1: Exact hyphenated match (expected format)
        if filename == f"tiersense-processed-{date_hyphen}.ndjson":
            candidates.insert(0, filename)  # Highest priority
            
        # Priority 2: Compact date format (actual Filebeat output)
        elif filename == f"tiersense-processed-{date_compact}.ndjson":
            candidates.insert(0, filename)  # Also high priority
            
        # Priority 3: Rotated files with compact date (common Filebeat pattern)
        elif filename.startswith(f"tiersense-processed-{date_compact}-") and filename.endswith(".ndjson"):
            # Extract rotation number to sort properly
            try:
                rotation_part = filename.replace(f"tiersense-processed-{date_compact}-", "").replace(".ndjson", "")
                rotation_num = int(rotation_part) if rotation_part.isdigit() else 0
                candidates.append((filename, rotation_num))
            except:
                candidates.append((filename, 999))  # Put at end if can't parse
                
        # Priority 4: Rotated files with hyphenated date
        elif filename.startswith(f"tiersense-processed-{date_hyphen}-") and filename.endswith(".ndjson"):
            try:
                rotation_part = filename.replace(f"tiersense-processed-{date_hyphen}-", "").replace(".ndjson", "")
                rotation_num = int(rotation_part) if rotation_part.isdigit() else 0
                candidates.append((filename, rotation_num))
            except:
                candidates.append((filename, 999))
                
        # Priority 5: Any file containing the target date in any format
        elif date_hyphen in filename or date_compact in filename:
            candidates.append((filename, 998))  # Lower priority
    
    # Process candidates - handle both simple strings and tuples
    final_candidates = []
    rotation_files = []
    
    for candidate in candidates:
        if isinstance(candidate, tuple):
            rotation_files.append(candidate)
        else:
            final_candidates.append(candidate)
    
    # Sort rotation files by rotation number (ascending - use base file first)
    if rotation_files:
        rotation_files.sort(key=lambda x: x[1])
        # Add rotation files after exact matches
        final_candidates.extend([f[0] for f in rotation_files])
    
    # Sort by modification time (newest first) for files of same priority
    if final_candidates:
        final_candidates.sort(key=lambda f: os.path.getmtime(os.path.join(log_dir, f)), reverse=True)
        
    return final_candidates
    
    # Fallback to original logic if no files found
    expected = f"tiersense-processed-{date_hyphen}.ndjson"
    full_path = os.path.join(log_dir, expected)
    return [expected] if os.path.isfile(full_path) else []


def is_valid_file_path(path: str, prefix: str) -> bool:
    """Check if path is a valid file that should be counted."""
    if not path:
        return False
    container_path = path
    if path.startswith(("/mnt/", "/home/", "/var/", "/opt/", "/data/")):
        container_path = f"/host-root{path}"
    if os.path.exists(container_path):
        if os.path.isdir(container_path):
            return False
    else:
        system_dirs = ['/bin','/usr','/etc','/var','/tmp','/proc','/sys','/dev','/run','/lib']
        if any(path.startswith(d) for d in system_dirs):
            return False
        temp_patterns = ['.lock','.tmp','.cache','.pid','.sock']
        if any(p in path.lower() for p in temp_patterns):
            return False
    if prefix:
        norm_pref = prefix.rstrip("/")
        norm_path = path.rstrip("/")
        if norm_path == norm_pref:
            return False
    return True


def get_file_stats(access_counts: Dict[str, int]) -> Dict[str, int]:
    """Get statistics about file access patterns."""
    if not access_counts:
        return {"total": 0, "hot": 0, "warm": 0, "cold": 0}
    counts = list(access_counts.values())
    hot_th, warm_th = 100, 20
    return {
        "total": len(counts),
        "hot":   sum(1 for c in counts if c >= hot_th),
        "warm":  sum(1 for c in counts if warm_th <= c < hot_th),
        "cold":  sum(1 for c in counts if c < warm_th),
        "max_access": max(counts),
        "min_access": min(counts),
        "avg_access": sum(counts) / len(counts),
    }


def cleanup_previous_day_logs(log_dir: str):
    """
    Remove any NDJSON files that do NOT match today's filename patterns,
    handling both expected format and actual Filebeat output formats.
    """
    try:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_compact = today.replace("-", "")
        
        for filename in os.listdir(log_dir):
            if filename.startswith("tiersense-processed") and filename.endswith(".ndjson"):
                # Keep today's files in any format including rotations
                should_keep = (
                    filename == f"tiersense-processed-{today}.ndjson" or  # Expected format
                    filename == f"tiersense-processed-{today_compact}.ndjson" or  # Compact format
                    filename.startswith(f"tiersense-processed-{today_compact}-") or  # Compact with rotation
                    filename.startswith(f"tiersense-processed-{today}-")  # Hyphenated with rotation
                )
                
                if not should_keep:
                    os.remove(os.path.join(log_dir, filename))
                    print(f"[INFO] Removed previous day log: {filename}")
    except Exception as e:
        print(f"[WARNING] Failed to cleanup previous day logs: {e}", file=sys.stderr)


def parse_logs(
    log_dir: str = "/app/logs",
    prefix: str = "",
    since: str = "",
    debug: bool = False,
    target_date: Optional[str] = None
) -> Dict[str, int]:
    """
    Parse audit logs and return file access counts.
    """
    if not os.path.isdir(log_dir):
        print(f"[ERROR] Log directory does not exist: {log_dir}", file=sys.stderr)
        return {}

    if target_date is None:
        cleanup_previous_day_logs(log_dir)

    log_files = find_log_files(log_dir, target_date)
    if not log_files:
        date_str = target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"[INFO] No NDJSON logs found for {date_str} in {log_dir}")
        return {}

    # Use the first (highest priority) log file
    latest_log = log_files[0]
    print(f"[INFO] Processing log: {latest_log}")
    full_path = os.path.join(log_dir, latest_log)
    start_ts = iso_to_dt(since) if since else None

    counts = {}
    total_good = total_bad = events_processed = 0
    event_buffer = defaultdict(lambda: {"cwd": [], "path": []})

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line_num, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    total_bad += 1
                    if debug:
                        print(f"[DEBUG] Malformed JSON at line {line_num}")
                    continue
                if start_ts:
                    ts = iso_to_dt(doc.get("@timestamp", ""))
                    if not ts or ts < start_ts:
                        continue
                msg = doc.get("message", "")
                if not msg:
                    continue
                audit_match = AUDIT_ID_RE.search(msg)
                if not audit_match:
                    continue
                event_id = audit_match.group(1)
                events_processed += 1
                if msg.startswith("type=CWD") or 'cwd="' in msg:
                    event_buffer[event_id]["cwd"].append(msg)
                elif "type=PATH" in msg or 'name="' in msg:
                    event_buffer[event_id]["path"].append(msg)
    except IOError as e:
        print(f"[ERROR] Failed to read log file {latest_log}: {e}", file=sys.stderr)
        return {}

    if debug:
        print(f"[DEBUG] Total events processed: {events_processed}")
        print(f"[DEBUG] Event buffer size: {len(event_buffer)}")

    for event_id, data in event_buffer.items():
        if debug and events_processed < 10:
            print(f"[DEBUG] Processing event {event_id}")
        cwd = ""
        for cwd_msg in data["cwd"]:
            m = FIELD_RES["cwd"].search(cwd_msg)
            if m:
                cwd = decode_escapes(m.group(1))
                break
        event_files = set()
        for path_msg in data["path"]:
            m = FIELD_RES["path"].search(path_msg)
            if not m:
                continue
            raw = decode_escapes(m.group(1))
            if not raw:
                continue
            abs_path = raw if raw.startswith(os.sep) else (
                os.path.normpath(os.path.join(cwd, raw)) if cwd else raw
            )
            if prefix and not abs_path.startswith(prefix):
                continue
            if not is_valid_file_path(abs_path, prefix):
                if debug:
                    print(f"[DEBUG] Skipping invalid path: {abs_path}")
                continue
            event_files.add(abs_path)
        for fp in event_files:
            counts[fp] = counts.get(fp, 0) + 1
            total_good += 1
            if debug and total_good <= 20:
                print(f"[DEBUG] Counted access to: {fp}")

    stats = get_file_stats(counts)
    print(f"[INFO] {latest_log}: {total_good} file accesses, {total_bad} malformed JSON lines")
    print(f"[SUMMARY] Unique files found: {len(counts)}")
    print(f"[SUMMARY] File distribution - HOT: {stats['hot']}, WARM: {stats['warm']}, COLD: {stats['cold']}")

    return counts


def parse_logs_with_daily_reset(
    log_dir: str = "/app/logs",
    prefix: str = "",
    debug: bool = False
) -> Dict[str, int]:
    """
    Parse logs with daily reset - each day starts with 0 access counts
    """
    # Ensure prior-day NDJSONs are removed before parsing today's file
    cleanup_previous_day_logs(log_dir)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    access_counts = parse_logs(
        log_dir=log_dir,
        prefix=prefix,
        debug=debug,
        target_date=today
    )
    if debug:
        print(f"[DEBUG] Daily reset parsing for {today}")
        print(f"[DEBUG] Found {len(access_counts)} files with fresh daily counts")
    return access_counts


def parse_logs_for_date(
    log_dir: str = "/app/logs",
    target_date: str = "",
    prefix: str = "",
    debug: bool = False
) -> Dict[str, int]:
    """
    Parse logs for a specific date.
    """
    return parse_logs(
        log_dir=log_dir,
        prefix=prefix,
        debug=debug,
        target_date=target_date
    )


def cleanup_old_logs(log_dir: str, days_to_keep: int = 7) -> None:
    """Clean up old log files, keeping only recent ones (daily reset version)."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        for filename in os.listdir(log_dir):
            if filename.endswith(".ndjson") and "tiersense-processed" in filename:
                file_path = os.path.join(log_dir, filename)
                file_time = datetime.fromtimestamp(
                    os.path.getctime(file_path), tz=timezone.utc
                )
                if file_time < cutoff_date:
                    os.remove(file_path)
                    print(f"[INFO] Cleaned up old log file: {filename}")
    except Exception as e:
        print(f"[WARNING] Failed to cleanup old logs: {e}", file=sys.stderr)


def get_today_counts_only() -> Dict[str, int]:
    """Get only today's access counts for daily reset functionality"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return parse_logs_with_daily_reset(prefix="", debug=False, log_dir="/app/logs")


# CLI interface for testing
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="TierSense NDJSON audit log parser with daily reset"
    )
    parser.add_argument(
        "-d", "--dir", default=os.getenv("LOG_DIR", "/app/logs"),
        help="Directory containing Filebeat NDJSON logs"
    )
    parser.add_argument("--prefix", default="", help="Only count paths beginning with this prefix")
    parser.add_argument("--since", default="", help="ISO timestamp; ignore events before this time")
    parser.add_argument("--date", default="", help="Parse logs for specific date (YYYY-MM-DD format)")
    parser.add_argument("--debug", action="store_true", help="Print debug information")
    parser.add_argument("--cleanup", action="store_true", help="Clean up old log files (older than 7 days)")
    parser.add_argument("--stats", action="store_true", help="Show detailed statistics")
    parser.add_argument("--daily-reset", action="store_true", help="Use daily reset mode (today's counts only)")
    args = parser.parse_args()

    if args.cleanup:
        cleanup_old_logs(args.dir, days_to_keep=7)

    if args.daily_reset:
        result = parse_logs_with_daily_reset(log_dir=args.dir, prefix=args.prefix, debug=args.debug)
        print("[INFO] Daily reset mode: showing only today's access counts")
    else:
        result = parse_logs(
            log_dir=args.dir,
            prefix=args.prefix,
            since=args.since,
            debug=args.debug,
            target_date=args.date or None
        )

    if args.stats and result:
        stats = get_file_stats(result)
        print("\n[STATS] Detailed Statistics:")
        print(f"[STATS] Total files: {stats['total']}")
        print(f"[STATS] HOT files (≥100 accesses): {stats['hot']}")
        print(f"[STATS] WARM files (20-99 accesses): {stats['warm']}")
        print(f"[STATS] COLD files (<20 accesses): {stats['cold']}")
        print(f"[STATS] Max accesses: {stats['max_access']}")
        print(f"[STATS] Min accesses: {stats['min_access']}")
        print(f"[STATS] Average accesses: {stats['avg_access']:.2f}")

    if args.debug:
        print("\n[DEBUG] Final results:")
        for path, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
            print(f"[DEBUG] {path}: {count}")

if __name__ == "__main__":
    main()