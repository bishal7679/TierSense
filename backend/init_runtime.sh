# #!/bin/bash
#init_runtime.sh

set -e

echo "[+] Generating Filebeat configuration..."

cat > /etc/filebeat/filebeat.yml <<EOF
filebeat.modules:
  - module: auditd
    log:
      enabled: true
      var.paths: ["/var/log/audit/audit.log"]

filebeat.autodiscover:
  providers:
    - type: docker
      hints.enabled: false

filebeat.config.modules:
  path: \${path.config}/modules.d/*.yml
  reload.enabled: false

output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
  codec.json:
    pretty: false
    escape_html: false

logging.to_files: true
logging.files:
  path: /app/logs
  name: filebeat.log
  keepfiles: 7
  permissions: 0644
EOF

echo "[+] Starting Filebeat in background..."
filebeat -e >> /app/logs/filebeat.log 2>&1 &

sleep 2

echo "[+] Starting FastAPI backend server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000