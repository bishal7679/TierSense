#!/bin/bash
set -e

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

echo "[✓] Base setup completed inside container."
