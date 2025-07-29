# Dockerfile for tiersense-backend (fixed auditctl access)

FROM python:3.12-slim

# 1. Install only auditctl (no daemon) and Filebeat dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    auditd \
    wget \
    gnupg \
    ca-certificates \
    procps \
    cron \
 && DEBIAN_FRONTEND=noninteractive systemctl mask auditd.service auditd.socket \
 && rm -rf /var/lib/apt/lists/*

# 2. Install Filebeat
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch \
     | gpg --dearmor -o /usr/share/keyrings/elastic.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
     > /etc/apt/sources.list.d/elastic-8.x.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends filebeat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Copy helper script and make executable
COPY scripts/tiersense_audit_config.sh /usr/local/bin/tiersense_audit_config.sh
RUN chmod +x /usr/local/bin/tiersense_audit_config.sh

# 4. Copy application requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy app code and runtime script
COPY ./app /app/app
COPY init_runtime.sh /init_runtime.sh
RUN chmod +x /init_runtime.sh

EXPOSE 8000

# 6. Entrypoint
CMD ["bash", "/init_runtime.sh"]