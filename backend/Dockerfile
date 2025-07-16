FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Copy scripts and env
COPY setup_base.sh /setup_base.sh
COPY init_runtime.sh /init_runtime.sh
COPY .env /app/.env
RUN chmod +x /setup_base.sh /init_runtime.sh

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

EXPOSE 8000

CMD ["/init_runtime.sh"]