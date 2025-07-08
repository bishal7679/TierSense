import os
from dotenv import load_dotenv

# Load .env file variables
load_dotenv()

# 1. Load directory where audit logs are stored
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# 2. Default LLM model for API
DEFAULT_LLM = os.getenv("LLM_PROVIDER", "gemini").lower()

# 3. Heatmap path: either from .env or fallback
HEATMAP_PATH = os.getenv("HEATMAP_PATH") or os.path.join(LOG_DIR, "access_heatmap.png")

# 4. Ensure target directory for heatmap exists
os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)

# 5. List of allowed LLM engines
SUPPORTED_LLMS = ["gemini", "gpt", "claude", "ollama", "copilot"]