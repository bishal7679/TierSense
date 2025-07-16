import os
from dotenv import load_dotenv

# Load .env if present (optional for local dev or overrides)
load_dotenv()

# 1. Path where Filebeat writes audit logs (.ndjson files)
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")  # Mounted as persistent Docker volume

# 2. Default LLM engine
DEFAULT_LLM = os.getenv("LLM_PROVIDER", "gemini").lower()

# 3. Heatmap output path inside volume
HEATMAP_PATH = os.getenv("HEATMAP_PATH", os.path.join(LOG_DIR, "access_heatmap.png"))
os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)

# 4. LLM support
SUPPORTED_LLMS = ["gemini", "gpt", "claude", "ollama", "copilot"]

# 5. Dynamic file path filtering (frontend user input)
def get_target_log_prefix():
    return os.getenv("TARGET_LOG_PREFIX", "/mnt")
