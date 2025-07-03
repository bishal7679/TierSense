import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Logging directory for parsed audit logs
LOG_DIR = os.getenv("LOG_DIR", "./logs")

# Default LLM provider (can be overridden by /run-tiering?llm=gpt etc.)
DEFAULT_LLM = os.getenv("LLM_PROVIDER", "gemini").lower()

# Heatmap output path
HEATMAP_PATH = os.path.join(LOG_DIR, "access_heatmap.png")

# Supported LLMs
SUPPORTED_LLMS = ["gemini", "gpt", "claude", "ollama", "copilot"]
