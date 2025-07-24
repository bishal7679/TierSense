# #!/bin/bash
#init_runtime.sh

set -e

echo "[+] Generating Filebeat configuration..."

 <<'EOF' > /etc/filebeat/filebeat.yml
filebeat.modules:
  - module: auditd
    log:
      enabled: true
      var:
        paths:
          - /var/log/audit/audit.log
  - module: auditd
    file:
      enabled: true
      var:
        paths:
          - /var/log/audit/audit.log

output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
  rotate_every_kb: 10240
  number_of_files: 50

filebeat.config.modules:
  path: ${path.config}/modules.d/*.yml
  reload.enabled: true
  reload.period: 10s
EOF

echo "[+] Starting Filebeat in background..."
filebeat -e >> /app/logs/filebeat.log 2>&1 &

sleep 2

echo "[+] Starting FastAPI backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000