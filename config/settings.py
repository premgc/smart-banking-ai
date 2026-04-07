import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
APP_DIR = ROOT_DIR / 'app'
DATA_DIR = ROOT_DIR / 'data'
VECTOR_STORE_DIR = ROOT_DIR / 'vector_store'

load_dotenv(ROOT_DIR / '.env')

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434').rstrip('/')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')
OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '60'))

QDRANT_MODE = os.getenv('QDRANT_MODE', 'local').lower()  # local | remote
QDRANT_HOST = os.getenv('QDRANT_HOST', 'localhost')
QDRANT_PORT = int(os.getenv('QDRANT_PORT', '6333'))
QDRANT_URL = os.getenv('QDRANT_URL', '').strip()
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'bank_data')
QDRANT_TIMEOUT = int(os.getenv('QDRANT_TIMEOUT', '30'))

EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
SEARCH_LIMIT = int(os.getenv('SEARCH_LIMIT', '8'))
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '700'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))
CSV_SKIPROWS = int(os.getenv('CSV_SKIPROWS', '10'))

STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
