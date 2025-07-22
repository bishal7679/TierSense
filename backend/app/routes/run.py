from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR
import os

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    log_directory: str = Form(None)
):
    """
    Parses logs from a directory (UI-provided or fallback),
    generates a heatmap, and returns LLM-based tiering advice.
    """
    try:
        # Determine directory to parse
        target_directory = log_directory.strip() if log_directory else LOG_DIR
        target_directory = os.path.abspath(target_directory)

        if not os.path.exists(target_directory):
            raise HTTPException(status_code=400, detail=f"Directory not found: {target_directory}")

        # Parse logs
        access_counts, _ = parse_logs(target_directory)

        if not access_counts:
            raise HTTPException(
                status_code=400,
                detail="No file access events found in logs. Interact with files and try again."
            )

        # Generate heatmap
        generate_heatmap(access_counts)

        # Get LLM output
        result = generate_tiering_suggestions(llm, access_counts, api_key)

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
