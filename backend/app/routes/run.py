# # app/routes/run.py

# import os
# import tempfile
# from typing import Optional

# from fastapi import APIRouter, UploadFile, File, Form, HTTPException
# from fastapi.responses import JSONResponse

# from app.core.parser import parse_logs
# from app.core.llm_factory import generate_tiering_suggestions

# router = APIRouter()

# @router.post("/run-tiering")
# async def run_tiering(
#     llm: str = Form(...),
#     api_key: str = Form(...),
#     file: Optional[UploadFile] = File(None)  # ✅ make file optional
# ):
#     tmp_path = None

#     try:
#         if file:
#             # ✅ If file uploaded, store to temp file
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp_file:
#                 tmp_file.write(await file.read())
#                 tmp_path = tmp_file.name
#             log_dir = os.path.dirname(tmp_path)

#         else:
#             # ✅ No file uploaded, use LOG_DIR from env (default: /var/log/filebeat_output)
#             log_dir = os.getenv("LOG_DIR", "/var/log/filebeat_output")

#         # 🔍 Run parser
#         access_counts, access_times = parse_logs(log_dir)

#         if not access_counts:
#             raise HTTPException(status_code=400, detail="No valid file accesses found in log")

#         # 🤖 Generate LLM tiering result
#         result = generate_tiering_suggestions(llm, access_counts)

#         return JSONResponse(content=result)

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     finally:
#         if tmp_path and os.path.exists(tmp_path):
#             os.remove(tmp_path)
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import os, tempfile

from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Case: default input → ignore uploaded file, use actual folder
        if file.filename == "empty.ndjson":
            log_dir = os.getenv("LOG_DIR", "/var/log/filebeat_output")
            access_counts, access_times = parse_logs(log_dir)

        # Case: file upload
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ndjson") as tmp_file:
                tmp_file.write(await file.read())
                tmp_path = tmp_file.name
            log_dir = os.path.dirname(tmp_path)
            access_counts, access_times = parse_logs(log_dir)
            os.remove(tmp_path)

        if not access_counts:
            raise HTTPException(status_code=400, detail="No valid file accesses found in log")

        result = generate_tiering_suggestions(llm, access_counts)
        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
