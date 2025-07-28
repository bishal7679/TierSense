from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from app.routes import run, settings, configure_monitoring
from app.config import HEATMAP_PATH
import os

app = FastAPI(
    title="TierSense LLM API",
    description="Backend API for TierSense File Access Tiering Advisor",
    version="1.0.0",
)

# Enable CORS for frontend (adjust origins in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health check
@app.get("/")
def read_root():
    return {"message": "TierSense API is running"}

# Mount all tiering‐related routes under /api
app.include_router(configure_monitoring.router)
app.include_router(run.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

# Expose heatmap under /api/heatmap
@app.get("/api/heatmap")
def get_heatmap():
    if os.path.exists(HEATMAP_PATH):
        return FileResponse(
            HEATMAP_PATH,
            media_type="image/png",
            filename="access_heatmap.png",
        )
    return {"error": "Heatmap file not found."}

# Disable caching on heatmap responses without altering the existing get_heatmap body
@app.middleware("http")
async def no_cache_heatmap(request, call_next):
    response = await call_next(request)
    if request.url.path == "/api/heatmap":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
