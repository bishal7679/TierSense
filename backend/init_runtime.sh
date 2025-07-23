#!/bin/bash
set -e

echo "[+] Preparing TierSense audit configuration script..."

# Ensure the audit script is executable
chmod +x /usr/local/bin/tiersense_audit_config.sh

# DO NOT run the audit config script at startup
# It will be invoked by FastAPI once the directory is selected

echo "[+] Generating Filebeat configuration..."

# Create Filebeat config using the default AUDIT_DIRECTORY or fallback
AUDIT_DIRECTORY="${AUDIT_DIRECTORY:-/host-root/nfs/logs}"

cat > /etc/filebeat/filebeat.yml <<EOF
filebeat.inputs:
- type: filestream
  id: audit_input
  enabled: true
  paths:
    - /var/log/audit/audit.log
  parsers:
    - multiline:
        type: pattern
        pattern: '^\\s*type='
        negate: true
        match: after
        max_lines: 5000
  fields:
    type: auditd
  multiline.timeout: 2s

output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
  codec.json:
    pretty: false
    escape_html: false
    
path.data: /var/lib/filebeat
EOF

echo "[+] Starting Filebeat in background..."
filebeat -e &

sleep 2

echo "[+] Starting FastAPI backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000