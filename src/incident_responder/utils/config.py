"""Utility functions for configuration management."""

import os
from pathlib import Path

import yaml
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
    CONFIG_DIR: Path = BASE_DIR / "config"
    SOURCES_CONFIG_PATH: Path = CONFIG_DIR / "sources.yaml"

    # API Settings
    API_HOST: str = os.getenv(ENV_API_HOST, DEFAULT_API_HOST)
    API_PORT: int = int(os.getenv(ENV_API_PORT, DEFAULT_API_PORT))

    # Sources configuration (loaded lazily)
    _sources_config: dict | None = None

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        cls.GIT_REPO_PATH.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_sources_config(cls) -> dict:
        """
        Load and return sources configuration from sources.yaml.

        Returns:
            Dictionary containing log_sources and git_sources configurations
        """
        if cls._sources_config is not None:
            return cls._sources_config

        default_config = {
            "log_sources": [
                {
                    "type": "local",
                    "enabled": True,
                    "config": {
                        "log_directory": str(cls.LOG_DIRECTORY),
                    },
                }
            ],
            "git_sources": [
                {
                    "type": "local",
                    "enabled": True,
                    "config": {
                        "repo_path": str(cls.GIT_REPO_PATH),
                    },
                }
            ],
        }

        if cls.SOURCES_CONFIG_PATH.exists():
            try:
                with open(cls.SOURCES_CONFIG_PATH) as f:
                    user_config = yaml.safe_load(f) or {}
                # Merge with defaults
                cls._sources_config = cls._merge_sources_config(default_config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load sources.yaml: {e}")
                cls._sources_config = default_config
        else:
            # Create default config file
            cls._sources_config = default_config
            cls._save_sources_config(default_config)

        return cls._sources_config

    @classmethod
    def _merge_sources_config(cls, default: dict, user: dict) -> dict:
        """Merge user config with defaults, preserving enabled status."""
        merged = default.copy()

        # Merge log sources
        if "log_sources" in user:
            for user_source in user["log_sources"]:
                user_type = user_source.get("type")
                # Find matching default source
                for i, default_source in enumerate(merged.get("log_sources", [])):
                    if default_source.get("type") == user_type:
                        # Update with user config, preserve enabled from user
                        merged["log_sources"][i] = {
                            **default_source,
                            **user_source,
                            "config": {
                                **default_source.get("config", {}),
                                **user_source.get("config", {}),
                            },
                        }
                        break
                else:
                    # New source type from user
                    merged["log_sources"].append(user_source)

        # Merge git sources
        if "git_sources" in user:
            for user_source in user["git_sources"]:
                user_type = user_source.get("type")
                for i, default_source in enumerate(merged.get("git_sources", [])):
                    if default_source.get("type") == user_type:
                        merged["git_sources"][i] = {
                            **default_source,
                            **user_source,
                            "config": {
                                **default_source.get("config", {}),
                                **user_source.get("config", {}),
                            },
                        }
                        break
                else:
                    merged["git_sources"].append(user_source)

        return merged

    @classmethod
    def _save_sources_config(cls, config: dict):
        """Save default sources config to file."""
        try:
            with open(cls.SOURCES_CONFIG_PATH, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Warning: Failed to create sources.yaml: {e}")

    @classmethod
    def get_enabled_log_source(cls) -> dict | None:
        """Get the first enabled log source configuration."""
        sources = cls.get_sources_config()
        for source in sources.get("log_sources", []):
            if source.get("enabled", False):
                return source
        return None

    @classmethod
    def get_enabled_git_source(cls) -> dict | None:
        """Get the first enabled git source configuration."""
        sources = cls.get_sources_config()
        for source in sources.get("git_sources", []):
            if source.get("enabled", False):
                return source
        return None


# Ensure directories on import
Config.ensure_directories()
