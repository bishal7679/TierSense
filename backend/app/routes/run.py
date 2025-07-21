# app/routes/run.py

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...)
):
    """
    Parses the processed logs from the /app/logs directory, generates a heatmap,
    and gets LLM-powered tiering suggestions.
    """
    try:
        # The log path is the directory where Filebeat is configured to save its output.
        log_directory = LOG_DIR  # This correctly points to "/app/logs"
        
        # The parser will scan this directory for all .ndjson files.
        access_counts, _ = parse_logs(log_directory)

        if not access_counts:
            raise HTTPException(
                status_code=400, 
                detail="No file access events were found. Please interact with files in the monitored directory and try again."
            )

        # Generate the heatmap based on the parsed access counts.
        generate_heatmap(access_counts)
        
        # Get the tiering suggestions from the selected LLM.
        result = generate_tiering_suggestions(llm, access_counts, api_key)
        
        return JSONResponse(content=result)

    except Exception as e:
        # Catch any unexpected errors during the process and report them.
        raise HTTPException(status_code=500, detail=str(e))