# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.routes import run, settings

# app = FastAPI(
#     title="TierSense LLM API",
#     description="Backend API for TierSense File Access Tiering Advisor",
#     version="1.0.0"
# )

# # Enable CORS for frontend (adjust origin in prod)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Replace with actual frontend domain in prod
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Register routes
# app.include_router(run.router, prefix="/api")
# app.include_router(settings.router, prefix="/api")

# @app.get("/")
# def read_root():
#     return {"message": "TierSense API is running"}

# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.routes import run, settings
from app.config import HEATMAP_PATH  # This will give us the heatmap file path
import os 

app = FastAPI(
    title="TierSense LLM API",
    description="Backend API for TierSense File Access Tiering Advisor",
    version="1.0.0"
)

# Enable CORS for frontend (adjust origin in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(run.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "TierSense API is running"}

@app.get("/api/heatmap")
def get_heatmap():
    if os.path.exists(HEATMAP_PATH):  # Check if heatmap file exists
        return FileResponse(HEATMAP_PATH, media_type="image/png", filename="access_heatmap.png")
    else:
        return {"error": "Heatmap file not found."}