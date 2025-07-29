# Use a minimal and secure base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy audit config helper script and make it executable
COPY scripts/tiersense_audit_config.sh /usr/local/bin/tiersense_audit_config.sh
RUN chmod +x /usr/local/bin/tiersense_audit_config.sh

# Install system dependencies (wget, procps, gpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gpg \
    procps \
    ca-certificates \
    gnupg \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install Filebeat from Elastic repo
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list && \
    apt-get update && apt-get install -y --no-install-recommends filebeat && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and runtime script
COPY ./app /app/app
COPY init_runtime.sh /init_runtime.sh
RUN chmod +x /init_runtime.sh

# Expose backend port
EXPOSE 8000

# Set container entrypoint
CMD ["bash", "/init_runtime.sh"]