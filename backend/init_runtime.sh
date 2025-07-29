#!/usr/bin/env bash
# backend/init_runtime.sh

set -euo pipefail

log() { echo -e "[INIT] $*"; }
die() { echo -e "[ERROR] $*" >&2; exit 1; }

# 1. Mount NFS (with better error handling)
if ! mountpoint -q /mnt/nfs; then
  [[ -z "${NFS_SERVER_IP:-}" || -z "${NFS_MOUNT_DIR:-}" ]] && die "NFS_SERVER_IP and NFS_MOUNT_DIR must be set"
  mkdir -p /mnt/nfs
  mount -t nfs -o ro,nolock,soft,timeo=10,retrans=3 "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs || die "Mount failed for ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
  log "Mounted NFS ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
else
  log "NFS already mounted at /mnt/nfs"
fi

# 2. Prepare logs directory
mkdir -p /app/logs
chmod 777 /app/logs
log "Prepared /app/logs"

# 3. Generate Filebeat config with FIXED daily file reset
cat <<'EOF' > /etc/filebeat/filebeat.yml
filebeat.modules:
- module: auditd
  log:
    enabled: true
    var.paths: ["/var/log/audit/audit.log"]
    scan.frequency: 1s
    close_inactive: 1s

output.file:
  enabled: true
  path: "/app/logs"
  filename: tiersense-processed-%{+yyyy-MM-dd}.ndjson
  rotate_every_kb: 104857600
  number_of_files: 7  # Keep only 7 days (1 week)
  rotate_on_startup: false  # FIXED: Don't create new file on restart

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: false  # FIXED: Disable to prevent config reload issues
  reload.period: 10s

# FIXED: Improved processors for daily reset
processors:
- timestamp:
    field: "@timestamp"
    layouts:
    - '2006-01-02T15:04:05.000Z'
    - '2006-01-02T15:04:05Z'
    - 'Jan _2 15:04:05'
    test:
    - '2025-07-29T12:17:30.123Z'
# REMOVED: drop_event processor that was filtering out events

logging.level: info
logging.to_files: true
logging.files:
  path: /app/logs
  name: filebeat
  keepfiles: 3
  rotateeverybytes: 10485760

EOF

log "Wrote Filebeat config with daily file rotation to /etc/filebeat/filebeat.yml"

# 4. Start Filebeat with better process management
log "Starting Filebeat with daily rotation"

# Kill any existing Filebeat processes
pkill -f filebeat || true
sleep 1

# Start Filebeat in background
nohup filebeat -e -c /etc/filebeat/filebeat.yml >> /app/logs/filebeat.log 2>&1 &
FILEBEAT_PID=$!

# Wait and verify startup
sleep 3
if kill -0 $FILEBEAT_PID 2>/dev/null; then
  log "Filebeat started successfully with PID $FILEBEAT_PID"
else
  log "Filebeat startup verification failed, checking logs..."
  tail -20 /app/logs/filebeat.log
  die "Filebeat failed to start; check /app/logs/filebeat.log"
fi

# 5. Ensure auditd is running (FIXED: Better service management)
if ! pgrep -x auditd >/dev/null; then
  log "Starting auditd service"
  # Try different methods to start auditd
  if command -v systemctl >/dev/null 2>&1; then
    systemctl start auditd || service auditd start || die "Failed to start auditd"
  else
    service auditd start || die "Failed to start auditd"
  fi
  log "auditd started successfully"
else
  log "auditd already running"
fi

# 6. ADDED: Create daily reset cleanup script
cat <<'EOF' > /usr/local/bin/daily_reset_cleanup.sh
#!/bin/bash
# Daily reset cleanup script - removes old files at midnight

TODAY=$(date +%Y-%m-%d)
LOG_DIR="/app/logs"

# Remove log files older than today (for daily reset)
find "$LOG_DIR" -name "tiersense-processed-*.ndjson" ! -name "*${TODAY}*" -delete 2>/dev/null || true

# Remove old heatmap files (keep only today's)
find "$LOG_DIR" -name "access_heatmap_*.png" -mtime +0 -delete 2>/dev/null || true

echo "[$(date)] Daily reset cleanup completed for $TODAY"
EOF

chmod +x /usr/local/bin/daily_reset_cleanup.sh
log "Created daily reset cleanup script"

# 7. ADDED: Setup cron job for daily reset (fallback)
echo "0 0 * * * /usr/local/bin/daily_reset_cleanup.sh >> /app/logs/daily_reset.log 2>&1" | crontab -
log "Setup daily reset cron job"

# 8. ADDED: Create audit rule validation
validate_audit_rules() {
  local rules_count=$(auditctl -l | wc -l)
  if [ "$rules_count" -eq 0 ]; then
    log "WARNING: No audit rules found. File access monitoring may not work."
    log "Make sure to configure monitoring through the TierSense UI."
  else
    log "Found $rules_count audit rules configured"
  fi
}

# Validate audit setup
validate_audit_rules

# 9. ADDED: Create initial daily log file
TODAY=$(date +%Y-%m-%d)
touch "/app/logs/tiersense-processed-${TODAY}.ndjson"
log "Created initial log file for today: $TODAY"

# 10. ADDED: Environment validation
log "Validating environment..."
log "- Log directory: /app/logs ($(ls -la /app/logs | wc -l) files)"
log "- NFS mount: /mnt/nfs ($(mountpoint /mnt/nfs && echo 'mounted' || echo 'not mounted'))"
log "- Host root mount: /host-root ($(ls /host-root >/dev/null 2>&1 && echo 'accessible' || echo 'not accessible'))"

# 11. Launch FastAPI with enhanced logging
log "Launching FastAPI with enhanced logging"
export PYTHONUNBUFFERED=1
export LOG_LEVEL=INFO

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --log-level info