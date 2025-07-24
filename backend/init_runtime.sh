# #!/bin/bash

set -e

echo "[+] Generating Filebeat configuration..."

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
filebeat -e >> /app/logs/filebeat.log 2>&1 &

sleep 2

echo "[+] Starting FastAPI backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000