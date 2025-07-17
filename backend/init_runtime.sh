#!/bin/bash
set -e

echo "[+] Running system setup (Filebeat, auditd, NFS)..."

# Start NFS support services
echo "[+] Starting NFS support services (rpcbind, nfs-common)..."
service rpcbind start
service nfs-common start
sleep 2

# Run the actual setup script (which already mounts NFS)
bash /setup_base.sh

echo "[+] Starting FastAPI backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
