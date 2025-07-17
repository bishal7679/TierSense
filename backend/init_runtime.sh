#!/bin/bash
set -e

echo "[+] Running system setup (Filebeat, auditd, NFS mount)..."

# Start NFS support services
echo "[+] Starting NFS support services (rpcbind, nfs-common)..."
service rpcbind start
service nfs-common start
sleep 2

# Run your existing base setup script
bash /setup_base.sh

# Mount NFS share
echo "[+] Mounting NFS share..."
mount -t nfs -o nolock "${NFS_SERVER}:${NFS_PATH}" "${NFS_MOUNT}"

echo "[+] Starting FastAPI backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
