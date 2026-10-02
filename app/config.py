from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    db_path: Path = ROOT / os.getenv("DB_PATH", "data/atlas.db")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "25"))
    max_pages_per_seed: int = int(os.getenv("MAX_PAGES_PER_SEED", "30"))
    max_depth: int = int(os.getenv("MAX_DEPTH", "2"))
    crawl_delay_seconds: float = float(os.getenv("CRAWL_DELAY_SECONDS", "0.25"))
    recent_days: int = int(os.getenv("RECENT_DAYS", "30"))
    user_agent: str = os.getenv("USER_AGENT", "AtlasScholarshipCrawler/1.0")
    use_ollama: bool = os.getenv("USE_OLLAMA", "false").lower() == "true"
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


SETTINGS = Settings()
SETTINGS.db_path.parent.mkdir(parents=True, exist_ok=True)
