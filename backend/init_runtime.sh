#!/bin/bash
set -e

# Run full system setup
/setup_base.sh

# Start FastAPI backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000