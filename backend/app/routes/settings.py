import os
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.config import SUPPORTED_LLMS, DEFAULT_LLM

router = APIRouter()

# Path is relative to the working directory inside the container
SETTINGS_FILE = "app/settings.json"


def load_settings() -> dict:
    """Load settings from disk, falling back to defaults on error or empty file."""
    if os.path.exists(SETTINGS_FILE):
        try:
            content = open(SETTINGS_FILE, "r").read().strip()
            if not content:
                return {}
            return json.loads(content)
        except (json.JSONDecodeError, IOError):
            # Corrupt or unreadable file: ignore and use defaults
            return {}
    return {}


def save_settings(data: dict):
    """Write settings atomically."""
    tmp_path = SETTINGS_FILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, SETTINGS_FILE)


@router.get("/settings")
def get_settings():
    """Return current settings including tier_ranges."""
    data = load_settings()
    return {
        "api_key": data.get("api_key", ""),
        "default_llm": data.get("default_llm", DEFAULT_LLM),
        "supported_llms": SUPPORTED_LLMS,
        "tier_ranges": data.get(
            "tier_ranges",
            {
                "HOT": [100, 999],
                "WARM": [20, 99],
                "COLD": [0, 19],
            },
        ),
    }


@router.post("/settings")
async def save_user_settings(request: Request):
    """Save API key, default LLM, and tier_ranges."""
    body = await request.json()
    api_key = body.get("api_key")
    default_llm = body.get("default_llm", DEFAULT_LLM)
    tier_ranges = body.get(
        "tier_ranges",
        {
            "HOT": [100, 999],
            "WARM": [20, 99],
            "COLD": [0, 19],
        },
    )

    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    if default_llm not in SUPPORTED_LLMS:
        raise HTTPException(status_code=400, detail="Invalid LLM provider")
    if (
        not isinstance(tier_ranges, dict)
        or set(tier_ranges.keys()) != {"HOT", "WARM", "COLD"}
        or not all(
            isinstance(v, list) and len(v) == 2 and
            (v[0] is None or isinstance(v[0], (int, float))) and
            (v[1] is None or isinstance(v[1], (int, float)))
            for v in tier_ranges.values()
        )
    ):
        raise HTTPException(status_code=400, detail="Invalid tier_ranges format")

    settings_data = {
        "api_key": api_key,
        "default_llm": default_llm,
        "tier_ranges": tier_ranges,
    }
    try:
        save_settings(settings_data)
        return JSONResponse(content={"message": "Settings saved successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save settings: {e}")
