FROM python:3.12-slim AS base

WORKDIR /app

# Install pipenv or use venv+requirements.txt
COPY requirements.txt ./

RUN python -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r --no-cache-dir  requirements.txt

COPY . .

EXPOSE 8000

CMD ["venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
