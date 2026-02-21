"""Utility functions for configuration management."""

import os
from pathlib import Path

from dotenv import load_dotenv

from ..constants import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_EMBEDDING_BASE_URL,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_GIT_REPO_PATH,
    DEFAULT_LOG_DIRECTORY,
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_REPORTS_DIRECTORY,
    ENV_API_HOST,
    ENV_API_PORT,
    ENV_EMBEDDING_BASE_URL,
    ENV_EMBEDDING_MODEL,
    ENV_GIT_REPO_PATH,
    ENV_LOG_DIRECTORY,
    ENV_OLLAMA_API_KEY,
    ENV_OLLAMA_BASE_URL,
    ENV_OLLAMA_MODEL,
    ENV_REPORTS_DIRECTORY,
)

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""

    # Ollama Cloud Settings (for main LLM agents)
    OLLAMA_MODEL: str = os.getenv(ENV_OLLAMA_MODEL, DEFAULT_OLLAMA_MODEL)
    OLLAMA_BASE_URL: str = os.getenv(ENV_OLLAMA_BASE_URL, DEFAULT_OLLAMA_BASE_URL)
    OLLAMA_API_KEY: str = os.getenv(ENV_OLLAMA_API_KEY, "")

    # Local Ollama Settings (for embeddings)
    EMBEDDING_MODEL: str = os.getenv(ENV_EMBEDDING_MODEL, DEFAULT_EMBEDDING_MODEL)
    EMBEDDING_BASE_URL: str = os.getenv(
        ENV_EMBEDDING_BASE_URL, DEFAULT_EMBEDDING_BASE_URL
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
