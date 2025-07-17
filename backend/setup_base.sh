#!/bin/bash
set -e

# Load env from .env
set -o allexport
source /app/.env
set +o allexport

if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set NFS_SERVER_IP and NFS_MOUNT_DIR in .env"
  exit 1
fi

echo "[+] Creating /mnt/nfs and mounting $NFS_SERVER_IP:$NFS_MOUNT_DIR..."
mkdir -p /mnt/nfs
mount -t nfs -o nolock ${NFS_SERVER_IP}:${NFS_MOUNT_DIR} /mnt/nfs


echo "[+] Creating persistent Docker volume path: /app/logs"
mkdir -p /app/logs
chmod 777 /app/logs

echo "[+] Writing Filebeat config to /etc/filebeat/filebeat.yml..."
cat <<EOF > /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/audit/audit.log
    processors:
      - decode_json_fields:
          fields: ["message"]
          target: ""
    multiline.pattern: '^{{'
    multiline.negate: true
    multiline.match: after

output.file:
  path: "/app/logs"
  filename: "access-tiering.ndjson"
  codec.json:
    pretty: false
EOF

echo "[+] Starting filebeat..."
filebeat -e &

echo "[✓] setup_base.sh complete!"