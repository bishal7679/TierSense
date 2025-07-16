#!/bin/bash
set -e

# Load env from mounted file (assumes Docker Compose binds /backend/.env into container)
if [[ -f ".env" ]]; then
  set -o allexport
  source .env
  set +o allexport
else
  echo "[✗] .env file not found inside container!"
  exit 1
fi

# Validate env
if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] Please set NFS_SERVER_IP and NFS_MOUNT_DIR in .env"
  exit 1
fi

echo "[+] Mounting NFS: $NFS_SERVER_IP:$NFS_MOUNT_DIR → /mnt/nfs"
mkdir -p /mnt/nfs
mount -t nfs "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs

echo "[+] Restarting filebeat for safety"
systemctl restart filebeat

echo "[✓] Runtime init complete. Starting FastAPI..."

# Launch FastAPI server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
