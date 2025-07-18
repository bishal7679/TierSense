#!/bin/bash
set -e

echo "[TierSense Setup] Starting base setup..."

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
mount -t nfs -o nolock "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs || {
  echo "[✗] Failed to mount NFS share. Check NFS server/export settings."
  exit 1
}

# Create persistent volume for logs
echo "[+] Ensuring persistent log path exists: /app/logs"
mkdir -p /app/logs
chmod 777 /app/logs

echo "[✓] Base setup complete. Waiting for UI to trigger monitoring setup."