# app/routes/run.py

import os
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),  # You can optionally use this for secure calls to LLMs
    file: UploadFile = File(...)
):
    try:
        # Save uploaded .ndjson file to temp dir
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp_file:
            tmp_file.write(await file.read())
            tmp_path = tmp_file.name

        # Set path for parser
        log_dir = os.path.dirname(tmp_path)
        access_counts, access_times = parse_logs(log_dir)

        if not access_counts:
            raise HTTPException(status_code=400, detail="No valid file accesses found in log")

        # Generate tiering advice
        result = generate_tiering_suggestions(llm, access_counts)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
