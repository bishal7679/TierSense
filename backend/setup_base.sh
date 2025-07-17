#!/bin/bash
set -e

# === Load environment from Docker-mounted .env ===
set -o allexport
source /app/.env
set +o allexport

# Validate essential vars
if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set NFS_SERVER_IP and NFS_MOUNT_DIR in .env"
  exit 1
fi

echo "[+] Installing system dependencies..."
apt update && apt install -y wget gnupg apt-transport-https curl software-properties-common

echo "[+] Adding Elastic GPG key and APT repository..."
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list
apt-get update

echo "[+] Installing filebeat, auditd, and nfs-common..."
apt update && apt install -y filebeat auditd nfs-common

echo "[+] Enabling auditd and filebeat..."
systemctl enable auditd
systemctl enable filebeat
systemctl start auditd
systemctl start filebeat

echo "[+] Creating /mnt/nfs and mounting $NFS_SERVER_IP:$NFS_MOUNT_DIR..."
mkdir -p /mnt/nfs
mount -t nfs "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs

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
  codec:
    format:
      string: '{"@timestamp":"%{@timestamp}","message":"%{[message]}"}'
EOF

echo "[+] Restarting filebeat to apply config..."
systemctl restart filebeat

echo "[✓] setup_base.sh complete!"
