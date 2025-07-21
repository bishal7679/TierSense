# Use a slim and official Python base image for a smaller footprint.
FROM python:3.12-slim

# Set the working directory inside the container. All subsequent commands will run from here.
WORKDIR /app

# Update package lists and install necessary tools in a single layer to optimize build time.
# - auditd: Provides the `auditctl` command needed to set monitoring rules on the host.
# - procps: Provides process utilities, useful for managing services like Filebeat.
RUN apt-get update && apt-get install -y --no-install-recommends \
    auditd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Download and install Filebeat, which will be used to collect and forward audit logs.
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list && \
    apt-get update && apt-get install -y filebeat && \
    rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's layer caching.
# This ensures dependencies are only re-installed if the requirements.txt file changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container.
COPY ./app /app/app

# Expose the port the FastAPI application will run on, making it accessible from the host.
EXPOSE 8000


# This is the command that will be run when the container starts.
# It starts Filebeat in the background and then starts the Uvicorn server for the FastAPI app.
CMD filebeat -e & uvicorn app.main:app --host 0.0.0.0 --port 8000