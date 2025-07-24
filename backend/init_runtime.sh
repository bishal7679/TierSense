#!/usr/bin/env bash
# backend/init_runtime.sh

set -euo pipefail

log()  { echo -e "[INIT] $*"; }
die()  { echo -e "[ERROR] $*" >&2; exit 1; }

# 1. Mount NFS
if ! mountpoint -q /mnt/nfs; then
  [[ -z "${NFS_SERVER_IP:-}" || -z "${NFS_MOUNT_DIR:-}" ]] && die "NFS vars required"
  mkdir -p /mnt/nfs
  mount -t nfs -o ro "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs || die "Mount failed"
  log "Mounted NFS ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
else
  log "NFS already mounted"
fi

# 2. Prepare logs
mkdir -p /app/logs && chmod 777 /app/logs

# 3. Generate Filebeat config
cat <<'EOF' > /etc/filebeat/filebeat.yml
filebeat.modules:
  - module: auditd
    log:
      enabled: true
      var.paths: ["/var/log/audit/audit.log"]
  - module: auditd
    file:
      enabled: true
      var.paths: ["/var/log/audit/audit.log"]
output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
  rotate_every_kb: 10240
  number_of_files: 50
filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: true
  reload.period: 10s
EOF

log "Starting Filebeat"
filebeat -e -c /etc/filebeat/filebeat.yml >> /app/logs/filebeat.log 2>&1 &

# 4. Start auditd
if ! pgrep -x auditd >/dev/null; then
  log "Starting auditd"
  service auditd start
else
  log "auditd running"
fi

# 5. Launch FastAPI
log "Launching FastAPI"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers
