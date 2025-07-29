FROM python:3.12-slim

# 1. Prevent any services from starting at install time
COPY policy-rc.d /usr/sbin/policy-rc.d
RUN chmod +x /usr/sbin/policy-rc.d

# 2. Install only the auditctl client (auditd package) and Filebeat dependencies
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      auditd \
      wget \
      gnupg \
      ca-certificates \
      procps \
      cron \
 && rm -rf /var/lib/apt/lists/*

# 3. Install Filebeat
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch \
     | gpg --dearmor -o /usr/share/keyrings/elastic.gpg \
 && echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" \
     > /etc/apt/sources.list.d/elastic-8.x.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends filebeat \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 4. Copy helper script and make executable
COPY scripts/tiersense_audit_config.sh /usr/local/bin/tiersense_audit_config.sh
RUN chmod +x /usr/local/bin/tiersense_audit_config.sh

# 5. Copy application requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy app code and runtime script
COPY ./app /app/app
COPY init_runtime.sh /init_runtime.sh
RUN chmod +x /init_runtime.sh

EXPOSE 8000

CMD ["bash", "/init_runtime.sh"]