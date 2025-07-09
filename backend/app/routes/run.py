# app/routes/run.py
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap  

router = APIRouter()
@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    tmp_path = None
    os.environ["OPENROUTER_API_KEY"] = api_key

    try:
        if file:
            # Save uploaded .ndjson file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp_file:
                tmp_file.write(await file.read())
                tmp_path = tmp_file.name
            log_file = tmp_path  # Use the file path, not the folder
        else:
            log_file = os.getenv("LOG_FILE_PATH", "/var/log/filebeat_output/access-tiering.json")

        access_counts, access_times = parse_logs(log_file)

        if not access_counts:
            raise HTTPException(status_code=400, detail="No valid file accesses found in log")

        generate_heatmap(access_counts)
        result = generate_tiering_suggestions(llm, access_counts, api_key)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
