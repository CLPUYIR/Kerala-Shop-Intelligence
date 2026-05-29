import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
DB_DIR.mkdir(exist_ok=True)

# Database Configuration
DB_PATH = DB_DIR / "kerala_shops.sqlite"
DB_URI = f"sqlite:///{DB_PATH}"

# Source Data
INPUT_CSV = r"C:\Users\abhis\Downloads\toddy_shops_final_master.csv"

# AI/LLM Configuration (Local Ollama)
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3" # or whichever model is available locally

# Scraping Configuration
MAX_CONCURRENT_PAGES = 3
HEADLESS_BROWSER = True
