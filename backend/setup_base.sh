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

echo "[+] Adding Elastic APT repo for Filebeat..."
apt update && apt install -y wget gnupg
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list
apt update

echo "[+] Installing dependencies: filebeat, auditd, nfs-common..."
apt install -y filebeat auditd nfs-common curl
