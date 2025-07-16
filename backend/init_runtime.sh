#!/bin/bash
set -e

echo "[+] Running system setup (Filebeat, auditd, NFS mount)..."
bash /setup_base.sh

echo "[+] Starting FastAPI backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
