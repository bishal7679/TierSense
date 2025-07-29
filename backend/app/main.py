from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from app.routes import run, settings, configure_monitoring
from app.config import HEATMAP_PATH
from app.core.daily_reset import start_background_scheduler, manual_reset  # Daily reset imports
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="TierSense LLM API",
    description="Backend API for TierSense File Access Tiering Advisor with Daily Reset",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start daily reset scheduler on app startup
@app.on_event("startup")
async def startup_event():
    """Initialize background services including daily reset scheduler"""
    try:
        start_background_scheduler()
        logger.info("TierSense API started with daily reset scheduler")
        logger.info("Daily reset will occur at 00:00 (midnight) daily")
        logger.info("Access counts will reset to 0 each day")
    except Exception as e:
        logger.error(f"Failed to start daily reset scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup background services on shutdown"""
    logger.info("TierSense API shutting down - daily reset scheduler stopped")

# Root health check
@app.get("/")
def read_root():
    return {
        "message": "TierSense API is running",
        "daily_reset": "active",
        "reset_time": "00:00 UTC"
    }

# Mount all tiering-related routes under /api
app.include_router(configure_monitoring.router)
app.include_router(run.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

# Dynamic heatmap serving by filename (fixes 404 errors)
@app.get("/api/heatmap/{filename}")
def get_heatmap_by_filename(filename: str):
    """Serve heatmap files by filename (for timestamped heatmaps)"""
    heatmap_dir = os.path.dirname(HEATMAP_PATH)
    file_path = os.path.join(heatmap_dir, filename)
    
    # Validate filename for security
    if not filename.startswith("access_heatmap_") or not filename.endswith(".png"):
        logger.warning(f"Invalid heatmap filename requested: {filename}")
        return {"error": "Invalid heatmap filename."}
    
    if not os.path.exists(file_path):
        logger.warning(f"Heatmap file not found: {file_path}")
        return {"error": "Heatmap file not found."}
    
    logger.info(f"Serving heatmap: {filename}")
    response = FileResponse(
        file_path,
        media_type="image/png",
        filename=filename,
    )
    
    # Disable caching for dynamic heatmaps
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Legacy endpoint for backwards compatibility
@app.get("/api/heatmap")
def get_default_heatmap():
    """Legacy endpoint - serves the default heatmap"""
    if not os.path.exists(HEATMAP_PATH):
        logger.warning(f"Default heatmap not found: {HEATMAP_PATH}")
        return {"error": "Heatmap file not found."}
    
    logger.info("Serving default heatmap")
    response = FileResponse(
        HEATMAP_PATH,
        media_type="image/png",
        filename="access_heatmap.png",
    )
    
    # Disable caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Alternative heatmap serving endpoint
@app.get("/api/heatmaps/{filename}")
def get_any_heatmap(filename: str):
    """Generic heatmap serving endpoint with enhanced security"""
    heatmap_dir = os.path.dirname(HEATMAP_PATH)
    file_path = os.path.join(heatmap_dir, filename)
    
    # Security: Only allow PNG files starting with 'access_heatmap_'
    if not (filename.endswith('.png') and 
            (filename.startswith('access_heatmap_') or filename == 'access_heatmap.png')):
        logger.warning(f"Access denied for file: {filename}")
        return {"error": "Access denied."}
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {filename}")
        return {"error": f"File {filename} not found."}
    
    return FileResponse(
        file_path,
        media_type="image/png",
        filename=filename,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Health check endpoint with daily reset status
@app.get("/api/health")
def health_check():
    """Enhanced health check endpoint that includes daily reset status"""
    try:
        # Check if logs directory exists
        logs_exist = os.path.exists("/app/logs")
        
        # Check if any heatmaps exist
        heatmap_dir = os.path.dirname(HEATMAP_PATH)
        heatmaps_exist = os.path.exists(heatmap_dir) and any(
            f.startswith("access_heatmap_") for f in os.listdir(heatmap_dir)
        )
        
        return {
            "status": "healthy",
            "service": "TierSense API",
            "version": "1.0.0",
            "daily_reset": {
                "enabled": True,
                "reset_time": "00:00 UTC",
                "description": "Access counts reset to 0 daily at midnight"
            },
            "storage": {
                "logs_directory": logs_exist,
                "heatmaps_available": heatmaps_exist,
                "retention_days": 7
            },
            "features": [
                "file_access_analysis",
                "llm_tiering_suggestions", 
                "dynamic_heatmaps",
                "historical_data",
                "daily_reset_scheduler",
                "automatic_cleanup"
            ]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# Manual reset endpoint for testing
@app.post("/api/manual-reset")
def trigger_manual_reset():
    """Manually trigger daily reset (for testing purposes)"""
    try:
        logger.info("Manual reset triggered")
        manual_reset()
        return {
            "status": "success", 
            "message": "Daily reset completed successfully",
            "timestamp": f"{os.environ.get('TZ', 'UTC')} time"
        }
    except Exception as e:
        logger.error(f"Manual reset failed: {e}")
        return {
            "status": "error",
            "message": f"Manual reset failed: {str(e)}"
        }

# System information endpoint
@app.get("/api/system")
def get_system_info():
    """Get system information for debugging"""
    try:
        log_dir = "/app/logs"
        log_files = []
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.ndjson')]
        
        heatmap_dir = os.path.dirname(HEATMAP_PATH)
        heatmap_files = []
        if os.path.exists(heatmap_dir):
            heatmap_files = [f for f in os.listdir(heatmap_dir) if f.startswith('access_heatmap_')]
        
        return {
            "log_directory": log_dir,
            "log_files": sorted(log_files),
            "heatmap_directory": heatmap_dir,
            "heatmap_files": sorted(heatmap_files),
            "daily_reset_active": True
        }
    except Exception as e:
        return {"error": str(e)}