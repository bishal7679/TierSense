from fastapi import APIRouter, Query
from app.core import parser, heatmap, llm_factory
from app.config import LOG_DIR, DEFAULT_LLM, SUPPORTED_LLMS

router = APIRouter()

@router.get("/run-tiering")
def run_tiering(llm: str = Query(default=DEFAULT_LLM)):
    llm = llm.lower()
    if llm not in SUPPORTED_LLMS:
        return {"error": f"LLM '{llm}' not supported. Choose from: {SUPPORTED_LLMS}"}

    access_counts, _ = parser.parse_logs(LOG_DIR)

    if not access_counts:
        return {"error": "No valid log data found for tiering."}

    heatmap.generate_heatmap(access_counts)
    result = llm_factory.generate_tiering_suggestions(llm, access_counts)

    return {
        "llm": llm,
        "tiering": result,
        "heatmap_path": f"/api/heatmap"  # exposed separately if needed
    }
