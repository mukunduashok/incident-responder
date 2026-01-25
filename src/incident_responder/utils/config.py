"""Utility functions for configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv

from ..constants import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_AZURE_API_VERSION,
    DEFAULT_AZURE_DEPLOYMENT_NAME,
    DEFAULT_GIT_REPO_PATH,
    DEFAULT_LOG_DIRECTORY,
    DEFAULT_REPORTS_DIRECTORY,
    ENV_API_HOST,
    ENV_API_PORT,
    ENV_AZURE_API_BASE,
    ENV_AZURE_API_KEY,
    ENV_AZURE_API_VERSION,
    ENV_AZURE_DEPLOYMENT_NAME,
    ENV_GIT_REPO_PATH,
    ENV_LOG_DIRECTORY,
    ENV_REPORTS_DIRECTORY,
)

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Azure OpenAI Settings
    AZURE_API_KEY: str = os.getenv(ENV_AZURE_API_KEY, "")
    AZURE_API_BASE: str = os.getenv(ENV_AZURE_API_BASE, "")
    AZURE_API_VERSION: str = os.getenv(ENV_AZURE_API_VERSION, DEFAULT_AZURE_API_VERSION)
    AZURE_DEPLOYMENT_NAME: str = os.getenv(
        ENV_AZURE_DEPLOYMENT_NAME, DEFAULT_AZURE_DEPLOYMENT_NAME
    )

    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    LOG_DIRECTORY: Path = BASE_DIR / os.getenv(ENV_LOG_DIRECTORY, DEFAULT_LOG_DIRECTORY)
    REPORTS_DIRECTORY: Path = BASE_DIR / os.getenv(
        ENV_REPORTS_DIRECTORY, DEFAULT_REPORTS_DIRECTORY
    )
    GIT_REPO_PATH: Path = BASE_DIR / os.getenv(ENV_GIT_REPO_PATH, DEFAULT_GIT_REPO_PATH)

    # API Settings
    API_HOST: str = os.getenv(ENV_API_HOST, DEFAULT_API_HOST)
    API_PORT: int = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.GIT_REPO_PATH.mkdir(parents=True, exist_ok=True)


# Ensure directories on import
Config.ensure_directories()
