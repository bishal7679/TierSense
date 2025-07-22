from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse

from app.core.parser import parse_logs
from app.core.llm_factory import generate_tiering_suggestions
from app.core.heatmap import generate_heatmap
from app.config import LOG_DIR  # default fallback

router = APIRouter()

@router.post("/run-tiering")
async def run_tiering(
    llm: str = Form(...),
    api_key: str = Form(...),
    log_directory: str = Form(None)
):
    """
    Parses logs from a directory (UI-provided or fallback),
    generates heatmap, and returns LLM-based tiering advice.
    """
    try:
        # Use UI-provided directory if available
        target_directory = log_directory if log_directory else LOG_DIR

        access_counts, _ = parse_logs(target_directory)

        if not access_counts:
            raise HTTPException(
                status_code=400,
                detail="No file access events found. Interact with files and try again."
            )

        generate_heatmap(access_counts)

        result = generate_tiering_suggestions(llm, access_counts, api_key)

        return JSONResponse(content=result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))