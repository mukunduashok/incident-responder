"""Utility functions for configuration management."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # LLM Settings
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3-coder")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_API_KEY: str = os.getenv("OLLAMA_API_KEY", "")
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    LOG_DIRECTORY: Path = BASE_DIR / os.getenv("LOG_DIRECTORY", "data/logs")
    REPORTS_DIRECTORY: Path = BASE_DIR / os.getenv("REPORTS_DIRECTORY", "reports")
    GIT_REPO_PATH: Path = BASE_DIR / os.getenv("GIT_REPO_PATH", "data/mock_repo")
    
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.GIT_REPO_PATH.mkdir(parents=True, exist_ok=True)


# Ensure directories on import
Config.ensure_directories()
