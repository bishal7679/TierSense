#!/bin/bash
set -e

# === Load .env ===
set -o allexport
source .env
set +o allexport

# Validate env
if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set NFS_SERVER_IP and NFS_MOUNT_DIR in your .env file"
  exit 1
fi

echo "[+] Installing dependencies: filebeat, auditd, nfs-common..."
apt update && \
apt install -y filebeat auditd nfs-common curl

echo "[+] Enabling and starting auditd and filebeat..."
systemctl enable auditd
systemctl enable filebeat
systemctl start auditd
systemctl start filebeat

echo "[+] Creating /app/logs directory (for Docker volume)..."
mkdir -p /app/logs
chmod 777 /app/logs

echo "[+] Mounting NFS share from $NFS_SERVER_IP:$NFS_MOUNT_DIR to /mnt/nfs..."
mkdir -p /mnt/nfs
mount -t nfs "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs

echo "[+] Persisting mount in /etc/fstab..."
echo "${NFS_SERVER_IP}:${NFS_MOUNT_DIR} /mnt/nfs nfs defaults 0 0" >> /etc/fstab

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
  codec:
    format:
      string: '{"@timestamp":"%{@timestamp}","message":"%{[message]}"}'
EOF

echo "[+] Restarting filebeat..."
systemctl restart filebeat

echo "[✓] NFS client + auditd + filebeat setup complete."
