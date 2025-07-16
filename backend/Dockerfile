# Use a minimal Python base
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Copy setup script and run it during build
COPY setup_base.sh /setup_base.sh
RUN chmod +x /setup_base.sh && /setup_base.sh

# Copy backend requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Runtime init + launch FastAPI
CMD ["/bin/bash", "/init_runtime.sh"]
