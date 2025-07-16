# Use a minimal Python image
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive
 
# Set the working directory
WORKDIR /app
 
# Copy and run setup script to install filebeat, auditd, nfs-common
COPY setup_base.sh /setup_base.sh
RUN chmod +x /setup_base.sh && /setup_base.sh

# Copy and load env file early (optional for debugging inside container)
COPY .env .env

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy all backend app files
COPY . .
 
# Expose backend port
EXPOSE 8000
 
# Run the FastAPI server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]