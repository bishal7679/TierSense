from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import run, settings

app = FastAPI(
    title="TierSense LLM API",
    description="Backend API for TierSense File Access Tiering Advisor",
    version="1.0.0"
)

# Enable CORS for frontend (adjust origin in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with actual frontend domain in prod
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
