from fastapi import APIRouter
from app.config import SUPPORTED_LLMS, DEFAULT_LLM

router = APIRouter()

@router.get("/llm-config")
def get_llm_config():
    return {
        "supported_llms": SUPPORTED_LLMS,
        "default_llm": DEFAULT_LLM
    }
