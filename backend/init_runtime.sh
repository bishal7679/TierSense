#!/usr/bin/env bash
# init_runtime.sh – improved to use host’s auditctl client only

set -euo pipefail
log() { echo "[INIT] $*"; }

# 1. Ensure /usr/sbin/auditctl is present (bind-mounted)
if ! command -v auditctl &>/dev/null; then
  log "ERROR: auditctl not found in container. Bind-mount /usr/sbin/auditctl from host."
  exit 1
fi

# 2. Mount NFS (unchanged)
if ! mountpoint -q /mnt/nfs; then
  [[ -z "${NFS_SERVER_IP:-}" || -z "${NFS_MOUNT_DIR:-}" ]] \
    && { log "NFS_SERVER_IP and NFS_MOUNT_DIR must be set"; exit 1; }
  mkdir -p /mnt/nfs
  mount -t nfs -o ro,nolock,soft,timeo=10,retrans=3 \
    "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs \
    || { log "Mount failed"; exit 1; }
  log "Mounted NFS ${NFS_SERVER_IP}:${NFS_MOUNT_DIR}"
else
  log "NFS already mounted at /mnt/nfs"
fi

# 3. Prepare logs dir
mkdir -p /app/logs && chmod 777 /app/logs
log "Prepared /app/logs"

# 4. Write Filebeat config
cat <<'EOF' > /etc/filebeat/filebeat.yml

filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/audit/audit.log
  scan_frequency: 10s
  close_inactive: 5m
  multiline:
    pattern: '^\s'
    match: after
  fields:
    logtype: auditd

output.file:
  enabled: true
  path: "/app/logs"
  filename: "tiersense-processed-%{+YYYY-MM-dd}.ndjson"
  rotate_every_kb: 10485760   # 10 MB
  number_of_files: 7
  permissions: 0644

processors:
- add_host_metadata: {}
- timestamp:
    field: "@timestamp"
    layouts:
      - '2006-01-02T15:04:05.000Z'
      - '2006-01-02T15:04:05Z'
      - 'Jan _2 15:04:05'

logging.level: info
logging.to_files: true
logging.files:
  path: /app/logs
  name: filebeat
  keepfiles: 3
EOF
log "Wrote Filebeat config"

# 5. Start Filebeat
pkill -f filebeat || true
nohup filebeat -e -c /etc/filebeat/filebeat.yml >>/app/logs/filebeat.log 2>&1 &
sleep 3
if ! pgrep -f filebeat >/dev/null; then
  log "Filebeat failed to start; check logs"
  exit 1
fi
log "Filebeat started"

# 6. Validate audit rules
RULES_COUNT=$(auditctl -l | wc -l)
if [ "$RULES_COUNT" -eq 0 ]; then
  log "WARNING: No audit rules found. Configure via TierSense UI."
else
  log "Found $RULES_COUNT audit rules"
fi

# 7. Create today’s log file
TODAY=$(date +%Y-%m-%d)
touch /app/logs/tiersense-processed-${TODAY}.ndjson
log "Initialized log file for ${TODAY}"

# 8. Start FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --log-level info
