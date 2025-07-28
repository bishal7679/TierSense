import os
import sys
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, Optional

# Regex patterns for parsing audit messages
AUDIT_ID_RE = re.compile(r"msg=audit\((\d+\.\d+:\d+)\)")
HEX_RE = re.compile(r"(?:\\x[0-9a-fA-F]{2})+")
FIELD_RES = {
    "path": re.compile(r'name="([^"]+)"'),
    "cwd": re.compile(r'cwd="([^"]+)"'),
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

def find_log_files(log_dir: str, target_date: Optional[str] = None) -> list:
    """Find NDJSON log files for the specified date (or today if None)."""
    if target_date:
        date_hyphen = target_date  # Expected format: YYYY-MM-DD
        date_compact = target_date.replace("-", "")  # YYYYMMDD
    else:
        today = datetime.now(timezone.utc)
        date_hyphen = today.strftime("%Y-%m-%d")
        date_compact = today.strftime("%Y%m%d")
    
    all_logs = []
    for filename in os.listdir(log_dir):
        if (filename.endswith(".ndjson") and 
            "tiersense-processed" in filename and 
            (date_hyphen in filename or date_compact in filename)):
            all_logs.append(filename)
    
    return sorted(all_logs, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))

def is_valid_file_path(path: str, prefix: str) -> bool:
    """Check if path is a valid file that should be counted."""
    if not path or not os.path.exists(path):
        return False
    
    # Skip directories
    if os.path.isdir(path):
        return False
    
    # Skip the exact prefix directory and its variations
    if prefix:
        normalized_prefix = prefix.rstrip("/")
        normalized_path = path.rstrip("/")
        if (normalized_path == normalized_prefix or 
            path == prefix + "/" or 
            path == prefix):
            return False
    
    return True

def parse_logs(
    log_dir: str = "/app/logs",
    prefix: str = "",
    since: str = "",
    debug: bool = False,
    target_date: Optional[str] = None
) -> Dict[str, int]:
    """
    Parse audit logs and return file access counts.
    
    Args:
        log_dir: Directory containing NDJSON log files
        prefix: Only count files starting with this path prefix
        since: ISO timestamp to filter events (optional)
        debug: Enable debug output
        target_date: Specific date to parse (YYYY-MM-DD format, defaults to today)
    
    Returns:
        Dictionary mapping file paths to access counts
    """
    if not os.path.isdir(log_dir):
        print(f"[ERROR] Log directory does not exist: {log_dir}", file=sys.stderr)
        return {}

    # Find log files for the target date
    log_files = find_log_files(log_dir, target_date)
    
    if not log_files:
        date_str = target_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        print(f"[INFO] No NDJSON logs found for {date_str} in {log_dir}")
        return {}

    # Use the most recent log file
    latest_log = log_files[-1]
    print(f"[INFO] Processing log: {latest_log}")

    # Parse timestamp filter
    start_ts = iso_to_dt(since) if since else None
    
    # Track file access counts
    counts = {}
    total_good = total_bad = 0
    
    # Buffer audit events by event ID
    event_buffer = defaultdict(lambda: {"cwd": [], "path": []})
    full_path = os.path.join(log_dir, latest_log)
    
    # Read and parse log file
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
                
                # Apply timestamp filter
                if start_ts:
                    ts = iso_to_dt(doc.get("@timestamp", ""))
                    if not ts or ts < start_ts:
                        continue
                
                # Extract audit message
                msg = doc.get("message", "")
                if not msg:
                    continue
                
                # Extract audit event ID
                audit_match = AUDIT_ID_RE.search(msg)
                if not audit_match:
                    continue
                
                event_id = audit_match.group(1)
                
                # Classify and buffer audit messages
                if msg.startswith("type=CWD") or 'cwd="' in msg:
                    event_buffer[event_id]["cwd"].append(msg)
                elif "type=PATH" in msg or 'name="' in msg:
                    event_buffer[event_id]["path"].append(msg)
    
    except IOError as e:
        print(f"[ERROR] Failed to read log file {latest_log}: {e}", file=sys.stderr)
        return {}
    
    # Process buffered audit events
    for event_id, event_data in event_buffer.items():
        if debug:
            print(f"[DEBUG] Processing event {event_id}")
        
        # Extract working directory for this event
        cwd = ""
        for cwd_msg in event_data["cwd"]:
            match = FIELD_RES["cwd"].search(cwd_msg)
            if match:
                cwd = decode_escapes(match.group(1))
                break  # Use the first (usually only) CWD
        
        # Process all PATH messages in this event
        event_files = set()  # Deduplicate files within the same event
        
        for path_msg in event_data["path"]:
            match = FIELD_RES["path"].search(path_msg)
            if not match:
                continue
            
            raw_path = decode_escapes(match.group(1))
            if not raw_path:
                continue
            
            # Construct absolute path
            if raw_path.startswith(os.sep):
                abs_path = raw_path
            else:
                abs_path = os.path.normpath(os.path.join(cwd, raw_path))
            
            # Apply prefix filter
            if prefix and not abs_path.startswith(prefix):
                continue
            
            # Validate file path
            if not is_valid_file_path(abs_path, prefix):
                if debug:
                    print(f"[DEBUG] Skipping invalid/non-existent path: {abs_path}")
                continue
            
            event_files.add(abs_path)
        
        # Count each unique file once per event
        for file_path in event_files:
            counts[file_path] = counts.get(file_path, 0) + 1
            total_good += 1
            
            if debug:
                print(f"[DEBUG] Counted access to: {file_path}")
    
    print(f"[INFO] {latest_log}: {total_good} file accesses, {total_bad} malformed JSON lines")
    print(f"[SUMMARY] Unique files found: {len(counts)}")
    
    if debug and counts:
        print("[DEBUG] Top 10 accessed files:")
        for i, (path, count) in enumerate(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]):
            print(f"[DEBUG]   {i+1}. {path}: {count} accesses")
    
    return counts

def parse_logs_for_date(
    log_dir: str = "/app/logs",
    target_date: str = "",
    prefix: str = "",
    debug: bool = False
) -> Dict[str, int]:
    """
    Parse logs for a specific date.
    
    Args:
        log_dir: Directory containing log files
        target_date: Date in YYYY-MM-DD format
        prefix: Path prefix filter
        debug: Enable debug output
    
    Returns:
        Dictionary mapping file paths to access counts
    """
    return parse_logs(
        log_dir=log_dir,
        prefix=prefix,
        debug=debug,
        target_date=target_date
    )

# CLI interface for testing
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TierSense NDJSON audit log parser")
    parser.add_argument(
        "-d", "--dir", 
        default=os.getenv("LOG_DIR", "/app/logs"),
        help="Directory containing Filebeat NDJSON logs"
    )
    parser.add_argument(
        "--prefix", 
        default="",
        help="Only count paths beginning with this prefix"
    )
    parser.add_argument(
        "--since", 
        default="",
        help="ISO timestamp; ignore events before this time"
    )
    parser.add_argument(
        "--date",
        default="",
        help="Parse logs for specific date (YYYY-MM-DD format)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Print debug information"
    )
    
    args = parser.parse_args()
    
    result = parse_logs(
        log_dir=args.dir,
        prefix=args.prefix,
        since=args.since,
        debug=args.debug,
        target_date=args.date if args.date else None
    )
    
    if args.debug:
        print("\n[DEBUG] Final results:")
        for path, count in sorted(result.items(), key=lambda x: x[1], reverse=True):
            print(f"[DEBUG] {path}: {count}")

if __name__ == "__main__":
    main()