#!/bin/bash
set -e

echo "[+] Running TierSense audit configuration script..."

# Ensure the audit script is executable
chmod +x /usr/local/bin/tiersense_audit_config.sh

# Execute the audit rule script (AUDIT_DIRECTORY is from .env or defaults)
if [ -f /usr/local/bin/tiersense_audit_config.sh ]; then
    /usr/local/bin/tiersense_audit_config.sh
else
    echo "[-] Audit config script not found at /usr/local/bin/tiersense_audit_config.sh"
    exit 1
fi

echo "[+] Generating Filebeat configuration..."

# Create Filebeat config inside the container
cat > /etc/filebeat/filebeat.yml <<EOF
filebeat.inputs:
- type: filestream
  enabled: true
  paths:
    - ${AUDIT_DIRECTORY}/*.log*

output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
path.data: /var/lib/filebeat
EOF

echo "[+] Starting Filebeat in background..."
filebeat -e &

# Give Filebeat a moment to initialize
sleep 2

echo "[+] Starting FastAPI backend server..."
# Replace the current process with uvicorn (best practice in Docker)
exec uvicorn app.main:app --host 0.0.0.0 --port 8000