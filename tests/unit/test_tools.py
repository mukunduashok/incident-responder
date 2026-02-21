"""Unit tests for custom tools."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from src.incident_responder.constants import (
    DEFAULT_MAX_COMMITS,
    LOG_FILE_EXTENSION,
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_FILES_TO_DISPLAY,
    REPORT_FILENAME_EXTENSION,
    REPORT_FILENAME_PREFIX,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
)
from src.incident_responder.tools import (
    GitSearchTool,
    LogParserTool,
)


class TestLogParserTool:
    """Unit tests for LogParserTool."""

    def test_tool_has_correct_name(self):
        """Should have correct tool name."""
        tool = LogParserTool()
        assert tool.name == "log_parser"

    def test_tool_has_description(self):
        """Should have a description."""
        tool = LogParserTool()
        assert len(tool.description) > 0
        assert "log" in tool.description.lower()

    def test_tool_has_args_schema(self):
        """Should have args schema defined."""
        tool = LogParserTool()
        assert tool.args_schema is not None

    def test_handles_missing_log_file(self):
        """Should handle missing log files gracefully."""
        tool = LogParserTool()
        result = tool._run(
            service_name="nonexistent-service-xyz", timestamp="2026-01-23T14:00:00"
        )
        assert "error" in result.lower() or "not found" in result.lower()

    def test_handles_empty_service_name(self):
        """Should handle empty service name."""
        tool = LogParserTool()
        result = tool._run(service_name="", timestamp="2026-01-23T14:00:00")
        assert "error" in result.lower() or "not found" in result.lower()

    def test_truncates_long_error_messages(self):
        """Should truncate messages longer than MAX_ERROR_MESSAGE_LENGTH."""
        tool = LogParserTool()
        # Create a temporary log file with a very long error message
        long_message = "x" * (MAX_ERROR_MESSAGE_LENGTH + 100)
        log_content = f"2026-01-23 14:23:45 ERROR [test-service] {long_message}\n"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=LOG_FILE_EXTENSION, delete=False
        ) as f:
            f.write(log_content)
            temp_path = f.name

        try:
            # Mock the config to use our temp file
            with patch(
                "src.incident_responder.tools.log_parser_tool.Config.LOG_DIRECTORY",
                Path(temp_path).parent,
            ):
                service_name = Path(temp_path).stem
                result = tool._run(service_name=service_name, timestamp="2026-01-23")
                # The result should contain "..." indicating truncation
                assert "..." in result
        finally:
            Path(temp_path).unlink()

    def test_format_analysis_output_method_exists(self):
        """Should have _format_analysis_output helper method."""
        tool = LogParserTool()
        assert hasattr(tool, "_format_analysis_output")
        assert callable(tool._format_analysis_output)


class TestGitSearchTool:
    """Unit tests for GitSearchTool."""

    def test_tool_has_correct_name(self):
        """Should have correct tool name."""
        tool = GitSearchTool()
        assert tool.name == "git_search"

    def test_tool_has_description(self):
        """Should have a description."""
        tool = GitSearchTool()
        assert len(tool.description) > 0
        assert "git" in tool.description.lower()

    def test_tool_has_args_schema(self):
        """Should have args schema defined."""
        tool = GitSearchTool()
        assert tool.args_schema is not None

    def test_handles_nonexistent_repository(self):
        """Should handle nonexistent repositories."""
        tool = GitSearchTool()
        result = tool._run(
            git_repo_path="/nonexistent/path/to/repo",
            timestamp="2026-01-24T00:00:00",
            max_commits=5,
        )
        assert "error" in result.lower() or "not found" in result.lower()

    def test_handles_non_git_directory(self):
        """Should handle directories that are not git repositories."""
        tool = GitSearchTool()
        with tempfile.TemporaryDirectory() as temp_dir:
            result = tool._run(
                git_repo_path=temp_dir, timestamp="2026-01-24", max_commits=5
            )
            assert "error" in result.lower() or "not a valid git" in result.lower()

    def test_uses_default_max_commits(self):
        """Should use DEFAULT_MAX_COMMITS when not specified."""
        tool = GitSearchTool()
        # Check the default value in the schema
        schema_defaults = tool.args_schema.model_fields
        assert "max_commits" in schema_defaults
        assert schema_defaults["max_commits"].default == DEFAULT_MAX_COMMITS

    def test_assess_risk_method_exists(self):
        """Should have _assess_risk method."""
        tool = GitSearchTool()
        assert hasattr(tool, "_assess_risk")
        assert callable(tool._assess_risk)

    def test_assess_risk_identifies_high_risk_files(self):
        """Should identify high-risk file patterns."""
        tool = GitSearchTool()
        high_risk_files = [
            "database_migration.sql",
            "schema_changes.sql",
            "config.yaml",
            "requirements.txt",
        ]
        for file in high_risk_files:
            risk = tool._assess_risk([file], "Normal commit message")
            assert risk == RISK_LEVEL_HIGH

    def test_assess_risk_identifies_medium_risk_files(self):
        """Should identify medium-risk file patterns."""
        tool = GitSearchTool()
        medium_risk_files = [
            "api_routes.py",
            "endpoint_handler.py",
            "service.py",
            "middleware.py",
        ]
        for file in medium_risk_files:
            risk = tool._assess_risk([file], "Normal commit message")
            assert risk == RISK_LEVEL_MEDIUM

    def test_assess_risk_identifies_low_risk_files(self):
        """Should identify low-risk changes."""
        tool = GitSearchTool()
        low_risk_files = ["README.md", "documentation.txt", "tests/test_utils.py"]
        for file in low_risk_files:
            risk = tool._assess_risk([file], "Normal commit message")
            assert risk == RISK_LEVEL_LOW

    def test_assess_risk_checks_commit_message(self):
        """Should assess risk based on commit message keywords."""
        tool = GitSearchTool()
        high_risk_messages = [
            "CRITICAL: Fix production issue",
            "Hotfix for urgent bug",
            "BREAKING CHANGE: Update API",
        ]
        for message in high_risk_messages:
            risk = tool._assess_risk(["some_file.py"], message)
            assert risk == RISK_LEVEL_HIGH

    def test_get_changed_files_method_exists(self):
        """Should have _get_changed_files method."""
        tool = GitSearchTool()
        assert hasattr(tool, "_get_changed_files")
        assert callable(tool._get_changed_files)

    def test_format_commit_output_method_exists(self):
        """Should have _format_commit_output method."""
        tool = GitSearchTool()
        assert hasattr(tool, "_format_commit_output")
        assert callable(tool._format_commit_output)

    def test_format_commit_output_limits_files_displayed(self):
        """Should limit number of files displayed per commit."""
        tool = GitSearchTool()
        # Create a commit with many files
        many_files = [f"file_{i}.py" for i in range(MAX_FILES_TO_DISPLAY + 10)]
        commits = [
            {
                "hash": "abc12345",
                "author": "Test Author",
                "date": "2026-01-23",
                "message": "Test commit",
                "files_changed": many_files,
                "risk_level": RISK_LEVEL_LOW,
            }
        ]
        output = tool._format_commit_output("/test/repo", "2026-01-24", commits)
        # Should contain "... and X more" message
        assert "more" in output.lower()

    def test_format_commit_output_shows_all_files_if_few(self):
        """Should show all files if count is within limit."""
        tool = GitSearchTool()
        few_files = ["file1.py", "file2.py"]
        commits = [
            {
                "hash": "abc12345",
                "author": "Test Author",
                "date": "2026-01-23",
                "message": "Test commit",
                "files_changed": few_files,
                "risk_level": RISK_LEVEL_LOW,
            }
        ]
        output = tool._format_commit_output("/test/repo", "2026-01-24", commits)
        assert "file1.py" in output
        assert "file2.py" in output
        assert "more" not in output.lower()
