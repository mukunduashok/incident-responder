"""Utility functions for configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Azure OpenAI Settings
    AZURE_API_KEY: str = os.getenv("AZURE_API_KEY", "")
    AZURE_API_BASE: str = os.getenv("AZURE_API_BASE", "")
    AZURE_API_VERSION: str = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
    AZURE_DEPLOYMENT_NAME: str = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4")

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
