import os
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.config import SUPPORTED_LLMS, DEFAULT_LLM

router = APIRouter()

SETTINGS_FILE = "app/settings.json"  # can also move to /etc/tiersense/ if needed

# Utility: Load settings file
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {}

# Utility: Save settings to file
def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# GET: Load current settings, including tier_ranges
@router.get("/settings")
def get_settings():
    data = load_settings()
    return {
        "api_key": data.get("api_key", ""),
        "default_llm": data.get("default_llm", DEFAULT_LLM),
        "supported_llms": SUPPORTED_LLMS,
        "tier_ranges": data.get("tier_ranges", {
            "HOT": [100, None],
            "WARM": [20, 99],
            "COLD": [None, 19]
        })
    }

# POST: Save new settings (including tier_ranges)
@router.post("/settings")
async def save_user_settings(request: Request):
    try:
        body = await request.json()
        api_key = body.get("api_key")
        default_llm = body.get("default_llm", DEFAULT_LLM)
        tier_ranges = body.get("tier_ranges", {
            "HOT": [100, None],
            "WARM": [20, 99],
            "COLD": [None, 19]
        })
        if not api_key:
            raise HTTPException(status_code=400, detail="API key is required")

        # Basic validation for tier_ranges structure (optional—add more as needed)
        if not isinstance(tier_ranges, dict) or not all(k in tier_ranges for k in ("HOT", "WARM", "COLD")):
            raise HTTPException(status_code=400, detail="Invalid tier_ranges format.")

        settings_data = {
            "api_key": api_key,
            "default_llm": default_llm,
            "tier_ranges": tier_ranges
        }
        save_settings(settings_data)
        return JSONResponse(content={"message": "Settings saved successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {e}")
