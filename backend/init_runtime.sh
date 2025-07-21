#!/bin/bash
# This script is the entrypoint for the backend container.
# It configures and starts the Filebeat service in the background,
# then starts the main FastAPI web server.
set -e

echo "[+] Configuring and starting Filebeat service..."

# This creates the Filebeat configuration file inside the container.
# It tells Filebeat to read the host's audit logs (mounted at /var/log/audit)
# and write the processed logs to the persistent /app/logs volume.
cat > /etc/filebeat/filebeat.yml <<EOF
filebeat.inputs:
- type: filestream
  enabled: true
  paths:
    - /var/log/audit/audit.log*

output.file:
  path: "/app/logs"
  filename: "tiersense-processed.ndjson"
  
# This prevents Filebeat from creating its own data directory in the root filesystem.
path.data: /var/lib/filebeat
EOF

# Start the Filebeat service in the background. The '&' is crucial.
filebeat -e &

# Give Filebeat a moment to start up.
sleep 2

echo "[+] Starting FastAPI backend..."
# Start the main application. 'exec' replaces the shell process with the uvicorn process,
# which is a best practice for Docker containers.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
