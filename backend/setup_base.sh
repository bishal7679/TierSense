#!/bin/bash
# This script prepares the backend container's environment by ensuring
# necessary directories and mounts are available before the application starts.
set -e

echo "[TierSense Setup] Starting base setup..."

# --- Environment Variable Loading ---
# Load environment variables from the .env file located in the app's root.
# This is crucial for getting the NFS server details provided by the user.
if [[ ! -f /app/.env ]]; then
  echo "[✗] CRITICAL: .env file not found at /app/.env. Cannot proceed."
  exit 1
fi

set -o allexport
source /app/.env
set +o allexport

# --- Environment Variable Validation ---
# Ensure that the user has defined the required NFS variables.
if [[ -z "$NFS_SERVER_IP" || -z "$NFS_MOUNT_DIR" ]]; then
  echo "[✗] CRITICAL: Please set both NFS_SERVER_IP and NFS_MOUNT_DIR in your .env file."
  exit 1
fi

# --- NFS Mount Handling (Corrected Logic) ---
# This block ensures the NFS share is mounted. It first checks if Docker
# has already mounted it (which is the standard and expected behavior).
# If not, it falls back to attempting a manual mount. This prevents errors.

# Ensure the target mount point directory exists inside the container.
mkdir -p /mnt/nfs

# Check if /mnt/nfs is already a mount point.
if grep -qs '/mnt/nfs' /proc/mounts; then
    echo "[✓] NFS share at /mnt/nfs is already mounted (handled by Docker)."
else
    # If not mounted by Docker, attempt a manual mount as a fallback.
    echo "[+] Attempting to manually mount NFS share from ${NFS_SERVER_IP}:${NFS_MOUNT_DIR} to /mnt/nfs..."
    mount -t nfs -o nolock "${NFS_SERVER_IP}:${NFS_MOUNT_DIR}" /mnt/nfs || {
      echo "[✗] FAILED to manually mount NFS share. Please check your docker-compose.yml volumes and NFS server settings."
      exit 1
    }
    echo "[✓] Manual NFS mount successful."
fi


# --- Persistent Log Volume Setup ---
# This ensures the directory for storing historical analysis logs exists
# and is writable by the application. This path is mapped to a persistent
# Docker volume.
echo "[+] Ensuring persistent log path exists and is writable: /app/logs"
mkdir -p /app/logs
chmod 777 /app/logs

echo "[✓] Base setup complete. The container is ready."