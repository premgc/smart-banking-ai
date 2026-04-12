from dotenv import load_dotenv
import os
from pathlib import Path

# ✅ force correct path to root .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

print("ENDPOINT:", os.getenv("AZURE_SEARCH_ENDPOINT"))
print("KEY:", os.getenv("AZURE_SEARCH_KEY"))