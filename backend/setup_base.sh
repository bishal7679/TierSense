#!/bin/bash
set -e

# === Read environment ===
set -o allexport
source /app/.env
set +o allexport

if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set NFS_SERVER_IP and NFS_MOUNT_DIR in .env"
  exit 1
fi

echo "[+] Installing filebeat, auditd, and NFS client..."
apt update && apt install -y filebeat auditd nfs-common

echo "[+] Enabling services..."
systemctl enable auditd
systemctl enable filebeat
systemctl start auditd
systemctl start filebeat

echo "[+] Mounting NFS: $NFS_SERVER_IP:$NFS_MOUNT_DIR → /mnt/nfs"
mkdir -p /mnt/nfs
mount -t nfs "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs

echo "[+] Creating persistent log dir: /app/logs"
mkdir -p /app/logs
chmod 777 /app/logs

echo "[+] Writing filebeat config..."
cat <<EOF > /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/audit/audit.log

output.file:
  path: "/app/logs"
  filename: "access-tiering.ndjson"
EOF

echo "[✓] setup_base.sh completed."
