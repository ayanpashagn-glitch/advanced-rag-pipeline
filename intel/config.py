"""Server-only configuration; no API keys are returned to the browser."""
import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(os.getenv('DATA_DIR', 'data'))
    provider: str = os.getenv('AI_PROVIDER', 'ollama')
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://127.0.0.1:11434')
    chat_model: str = os.getenv('CHAT_MODEL', 'llama3.2:3b')
    embedding_model: str = os.getenv('EMBEDDING_MODEL', 'mxbai-embed-large')
    groq_model: str = os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant')
    groq_key: str = os.getenv('GROQ_API_KEY', '')
    max_bytes: int = 20 * 1024 * 1024
    max_pages: int = 100
    max_chars: int = 350_000
    max_docs: int = 12
    timeout: float = 120
