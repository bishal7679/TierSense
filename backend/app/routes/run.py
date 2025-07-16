# app/routes/run.py

import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    file: Optional[UploadFile] = File(None),
    target_dir: Optional[str] = Form(None)
):
    tmp_path = None
    os.environ["OPENROUTER_API_KEY"] = api_key

    try:
        # Step 1: Normalize and apply custom prefix
        if target_dir:
            clean_dir = target_dir.strip()
            if not clean_dir.startswith("/"):
                clean_dir = "/" + clean_dir
            os.environ["TARGET_LOG_PREFIX"] = clean_dir
        else:
            os.environ["TARGET_LOG_PREFIX"] = "/mnt"

        print(f"[INFO] Using target path prefix: {os.environ['TARGET_LOG_PREFIX']}")

        # Step 2: Handle uploaded .ndjson or mounted volume logs
        if file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp_file:
                tmp_file.write(await file.read())
                tmp_path = tmp_file.name
            log_path = tmp_path
        else:
            log_path = LOG_DIR  # /app/logs

        # Step 3: Parse logs + generate heatmap
        access_counts, access_times = parse_logs(log_path)

        if not access_counts:
            raise HTTPException(status_code=400, detail="No valid file accesses found in log")

        generate_heatmap(access_counts)

        # Step 4: Invoke LLM for tiering recommendation
        result = generate_tiering_suggestions(llm, access_counts, api_key)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)