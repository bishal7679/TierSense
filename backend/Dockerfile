# Use a slim and official Python base image for a smaller footprint.
FROM python:3.12-slim

# Set the working directory inside the container.
WORKDIR /app

# --- Install All System Dependencies in a Single Layer ---
# This is the corrected step. We install all necessary tools (wget, gpg, auditd)
# in one go to ensure they are available for subsequent commands and to optimize the build.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gpg \
    auditd \
    procps \
    && rm -rf /var/lib/apt/lists/*

# --- Install Filebeat ---
# Now that wget and gpg are installed, this command will succeed.
RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" | tee /etc/apt/sources.list.d/elastic-8.x.list && \
    apt-get update && apt-get install -y filebeat && \
    rm -rf /var/lib/apt/lists/*

# --- Install Python Dependencies ---
# Copy only the requirements file first to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy Application Code and Scripts ---
COPY ./app /app/app
COPY init_runtime.sh /init_runtime.sh
RUN chmod +x /init_runtime.sh

# Expose the port the FastAPI application will run on.
EXPOSE 8000

# Set the entrypoint for the container.
CMD ["bash", "/init_runtime.sh"]