from fastapi import APIRouter, Query
from app.core.parser import parse_logs
from app.core.heatmap import generate_heatmap
from app.core.llm_factory import generate_tiering_suggestions as get_llm_response
import os

router = APIRouter()

@router.get("/run-tiering")
def run_tiering(llm: str = Query("gemini")):
    log_dir = os.getenv("LOG_DIR", "/mnt/nfs-logs")
    access_counts, access_times = parse_logs(log_dir)

    if not access_counts:
        return {"error": "No access data found."}

    generate_heatmap(access_counts)
    tiering = get_llm_response(llm, access_counts)

    return {
        "tiering": tiering,
        "heatmap": "/api/heatmap"
    }
