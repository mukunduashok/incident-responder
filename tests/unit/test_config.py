"""Unit tests for configuration module."""

from pathlib import Path

import pytest

from src.incident_responder.utils.config import Config


class TestConfigClass:
    """Test Config class and its properties."""

    def test_config_has_ollama_settings(self):
        """Config should have Ollama settings."""
        assert hasattr(Config, "OLLAMA_MODEL")
        assert hasattr(Config, "OLLAMA_BASE_URL")
        assert hasattr(Config, "OLLAMA_API_KEY")

    def test_config_has_path_settings(self):
        """Config should have path settings."""
        assert hasattr(Config, "BASE_DIR")
        assert hasattr(Config, "LOG_DIRECTORY")
        assert hasattr(Config, "REPORTS_DIRECTORY")
        assert hasattr(Config, "GIT_REPO_PATH")

    def test_config_has_api_settings(self):
        """Config should have API settings."""
        assert hasattr(Config, "API_HOST")
        assert hasattr(Config, "API_PORT")

    def test_base_dir_is_path(self):
        """BASE_DIR should be a Path object."""
        assert isinstance(Config.BASE_DIR, Path)
        assert Config.BASE_DIR.exists()

    def test_log_directory_is_path(self):
        """LOG_DIRECTORY should be a Path object."""
        assert isinstance(Config.LOG_DIRECTORY, Path)

    def test_reports_directory_is_path(self):
        """REPORTS_DIRECTORY should be a Path object."""
        assert isinstance(Config.REPORTS_DIRECTORY, Path)

    def test_git_repo_path_is_path(self):
        """GIT_REPO_PATH should be a Path object."""
        assert isinstance(Config.GIT_REPO_PATH, Path)

    def test_api_port_is_integer(self):
        """API_PORT should be an integer."""
        assert isinstance(Config.API_PORT, int)

    def test_api_port_in_valid_range(self):
        """API_PORT should be in valid range (1-65535)."""
        assert 1 <= Config.API_PORT <= 65535


class TestConfigDirectories:
    """Test directory creation and management."""

    def test_ensure_directories_method_exists(self):
        """Config should have ensure_directories method."""
        assert hasattr(Config, "ensure_directories")
        assert callable(Config.ensure_directories)

    def test_log_directory_exists(self):
        """Log directory should exist after config initialization."""
        assert Config.LOG_DIRECTORY.exists()

    def test_reports_directory_exists(self):
        """Reports directory should exist after config initialization."""
        assert Config.REPORTS_DIRECTORY.exists()

    def test_git_repo_path_exists(self):
        """Git repo path should exist after config initialization."""
        assert Config.GIT_REPO_PATH.exists()

    def test_ensure_directories_is_idempotent(self):
        """Calling ensure_directories multiple times should be safe."""
        # Should not raise any exceptions
        Config.ensure_directories()
        Config.ensure_directories()
        assert Config.LOG_DIRECTORY.exists()


class TestConfigPaths:
    """Test path calculations and relationships."""

    def test_all_paths_are_absolute(self):
        """All path configurations should be absolute paths."""
        assert Config.BASE_DIR.is_absolute()
        assert Config.LOG_DIRECTORY.is_absolute()
        assert Config.REPORTS_DIRECTORY.is_absolute()
        assert Config.GIT_REPO_PATH.is_absolute()

    def test_paths_are_within_project(self):
        """Directories should be within the project BASE_DIR."""
        base = Config.BASE_DIR
        # LOG_DIRECTORY and REPORTS_DIRECTORY should be within BASE_DIR
        try:
            Config.LOG_DIRECTORY.relative_to(base)
            Config.REPORTS_DIRECTORY.relative_to(base)
            Config.GIT_REPO_PATH.relative_to(base)
        except ValueError:
            pytest.fail("Paths should be within BASE_DIR")
