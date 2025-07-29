#!/usr/bin/env bash
# backend/init_runtime.sh

set -euo pipefail

log()  { echo -e "[INIT] $*"; }
die()  { echo -e "[ERROR] $*" >&2; exit 1; }

# 1. Mount NFS
if ! mountpoint -q /mnt/nfs; then
  [[ -z "${NFS_SERVER_IP:-}" || -z "${NFS_MOUNT_DIR:-}" ]] && die "NFS_SERVER_IP and NFS_MOUNT_DIR must be set"
  mkdir -p /mnt/nfs
  mount -t nfs -o ro "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs || die "Mount failed for ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
  log "Mounted NFS ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
else
  log "NFS already mounted at /mnt/nfs"
fi

# 2. Prepare logs directory
mkdir -p /app/logs
chmod 777 /app/logs
log "Prepared /app/logs"

# 3. Generate Filebeat config with daily file rotation
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
  filename: tiersense-processed.ndjson
  # large file size limit to keep all daily logs in one file
  rotate_every_kb: 524288  # 512MB per file
  number_of_files: 30      # Keep 30 days of files
  # Force new file creation on startup
  rotate_on_startup: true

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: true
  reload.period: 10s

# Enable date-based processing
processors:
  - timestamp:
      field: "@timestamp"
      layouts:
        - '2006-01-02T15:04:05.000Z'
      test:
        - '2025-07-26T12:17:30.123Z'
EOF
log "Wrote Filebeat config with daily file rotation to /etc/filebeat/filebeat.yml"

# 4. Start Filebeat
log "Starting Filebeat with daily rotation"
filebeat -e -c /etc/filebeat/filebeat.yml >> /app/logs/filebeat.log 2>&1 &
sleep 2
if pgrep -x filebeat >/dev/null; then
  log "Filebeat started successfully with daily file rotation"
else
  die "Filebeat failed to start; check /app/logs/filebeat.log"
fi

# 5. Start auditd (host-managed via helper, ensure running)
if ! pgrep -x auditd >/dev/null; then
  log "Starting auditd service"
  service auditd start || die "Failed to start auditd"
else
  log "auditd already running"
fi

# 6. Launch FastAPI
log "Launching FastAPI"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers