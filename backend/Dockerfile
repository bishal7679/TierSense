# FROM python:3.12-slim

# ENV DEBIAN_FRONTEND=noninteractive

# WORKDIR /app

# # Copy setup scripts
# COPY setup_base.sh /setup_base.sh
# COPY init_runtime.sh /init_runtime.sh
# RUN chmod +x /setup_base.sh /init_runtime.sh

# # Install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy backend application code
# COPY . .

# # Expose FastAPI port
# EXPOSE 8000

# # Run init script which mounts NFS and launches backend
# CMD ["/init_runtime.sh"]

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# --- Install required system packages ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    curl \
    apt-transport-https \
    software-properties-common \
    auditd \
    nfs-common \
    && rm -rf /var/lib/apt/lists/*

# Add Elastic repo (GPG key + repo) and install Filebeat only once
RUN curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg && \
    echo "deb [trusted=yes] https://artifacts.elastic.co/packages/7.x/apt stable main" \
    > /etc/apt/sources.list.d/elastic-7.x.list && \
    apt-get update && apt-get install -y filebeat rpcbind && \
    rm -rf /var/lib/apt/lists/*

# --- Copy app and scripts ---
COPY setup_base.sh /setup_base.sh
COPY init_runtime.sh /init_runtime.sh
COPY requirements.txt .
RUN chmod +x /setup_base.sh /init_runtime.sh

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create logs folder
RUN mkdir -p /app/logs

EXPOSE 8000

CMD ["/init_runtime.sh"]
