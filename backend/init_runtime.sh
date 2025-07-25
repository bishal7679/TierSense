#!/usr/bin/env bash
# backend/init_runtime.sh

set -euo pipefail

log()  { echo -e "[INIT] $*"; }
die()  { -e "[ERROR] $*" >&2; exit 1; }

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

# 3. Generate Filebeat config
cat <<'EOF' > /etc/filebeat/filebeat.yml
filebeat.modules:
  - module: auditd
    log:
      enabled: true
      var.paths: ["/var/log/audit/audit.log"]

output.file:
  enabled: true
  path: "/app/logs"
  filename: "tiersense-processed-%{+yyyy-MM-dd}.ndjson"
  rotate_every_kb: 10240
  number_of_files: 3
  rotate_on_startup: true

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: true
  reload.period: 10s
EOF
log "Wrote Filebeat config to /etc/filebeat/filebeat.yml"

# 4. Start Filebeat
log "Starting Filebeat"
filebeat -e -c /etc/filebeat/filebeat.yml >> /app/logs/filebeat.log 2>&1 &
sleep 1
if pgrep -x filebeat >/dev/null; then
  log "Filebeat started successfully"
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