import os
from dotenv import load_dotenv

# Load .env file if present (useful for local development or defaults)
load_dotenv()

# --- 1. Filebeat log directory ---
LOG_DIR = os.getenv("LOG_DIR", "/app/logs")  # This path should be mounted in Docker volume

# --- 2. Default LLM provider ---
DEFAULT_LLM = os.getenv("LLM_PROVIDER", "gemini").lower()

# --- 3. Heatmap path (auto-create parent if needed) ---
HEATMAP_PATH = os.getenv("HEATMAP_PATH", os.path.join(LOG_DIR, "access_heatmap.png"))
os.makedirs(os.path.dirname(HEATMAP_PATH), exist_ok=True)

# --- 4. Supported LLMs ---
SUPPORTED_LLMS = ["gemini", "gpt", "claude", "ollama", "copilot"]

# --- 5. Runtime audit directory file (set by UI) ---
RUNTIME_AUDIT_PATH_FILE = os.path.join(LOG_DIR, "current_audit_path.txt")

# --- 6. Resolved Audit Directory ---
def get_audit_directory():
    """Returns the audit directory path set by UI or falls back to .env value."""
    if os.path.exists(RUNTIME_AUDIT_PATH_FILE):
        with open(RUNTIME_AUDIT_PATH_FILE, "r") as f:
            path = f.read().strip()
            if path:
                return path
    return os.getenv("AUDIT_DIRECTORY", "/host-root/nfs/logs")

# --- 7. Target log prefix filter ---
def get_target_log_prefix():
    """Returns a path prefix used to filter logs, default is /mnt"""
    return os.getenv("TARGET_LOG_PREFIX", "/mnt")