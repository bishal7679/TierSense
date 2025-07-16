FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Copy setup scripts
COPY setup_base.sh /setup_base.sh
COPY init_runtime.sh /init_runtime.sh
RUN chmod +x /setup_base.sh /init_runtime.sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run init script which mounts NFS and launches backend
CMD ["/init_runtime.sh"]