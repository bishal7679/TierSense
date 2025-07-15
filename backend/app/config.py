import os
from dotenv import load_dotenv

# Load .env file variables
load_dotenv()

# 1. Directory where audit logs (ndjson) are stored
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# 2. Default LLM model
DEFAULT_LLM = os.getenv("LLM_PROVIDER", "gemini").lower()

# 3. Heatmap output path
HEATMAP_PATH = os.getenv("HEATMAP_PATH") or os.path.join(LOG_DIR, "access_heatmap.png")
os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)

# 4. Allowed LLM engines
SUPPORTED_LLMS = ["gemini", "gpt", "claude", "ollama", "copilot"]

# 5. Config file for selected directory to parse
SELECTED_PATH_FILE = "/app/config/selected_path.txt"

# 6. Function to get current target directory (e.g., /mnt/data)
def get_target_log_prefix():
    try:
        with open(SELECTED_PATH_FILE) as f:
            path = f.read().strip()
            if os.path.isdir(path):
                return path
    except FileNotFoundError:
        pass
    return os.getenv("TARGET_LOG_PREFIX", "/mnt/data")
