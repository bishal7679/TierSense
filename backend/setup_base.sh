#!/bin/bash
set -e

# Load environment variables from .env
if [[ ! -f /app/.env ]]; then
  echo "[✗] .env file not found at /app/.env"
  exit 1
fi

set -o allexport
source /app/.env
set +o allexport

# Validate required environment variables
if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set both NFS_SERVER_IP and NFS_MOUNT_DIR in .env"
  exit 1
fi

# Mount NFS share
echo "[+] Mounting NFS share from ${NFS_SERVER_IP}:${NFS_MOUNT_DIR} to /mnt/nfs..."
mkdir -p /mnt/nfs
mount -t nfs -o nolock "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs

# Create persistent volume for logs
echo "[+] Ensuring persistent log path exists: /app/logs"
mkdir -p /app/logs
chmod 777 /app/logs

# Write Filebeat configuration
echo "[+] Writing Filebeat config to /etc/filebeat/filebeat.yml"
cat <<EOF > /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /mnt/nfs/*.ndjson
    processors:
      - decode_json_fields:
          fields: ["message"]
          target: ""
          overwrite_keys: true
    multiline.pattern: '^{{'
    multiline.negate: true
    multiline.match: after

output.file:
  path: "/app/logs"
  filename: "access-tiering.ndjson"
  codec.json:
    pretty: false
EOF

# Start Filebeat in background
echo "[+] Starting Filebeat..."
filebeat -e &

echo "[✓] setup_base.sh complete!"
