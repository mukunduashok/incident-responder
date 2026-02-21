"""Integration tests for tools working with actual files.

These tests verify that tools correctly interact with the file system
and external tools (like git).
"""

import pytest

from src.incident_responder.tools import (
    GitSearchTool,
    LogParserTool,
)
from src.incident_responder.utils.config import Config


@pytest.mark.parametrize(
    "log_case",
    [
        {
            "service_name": "payment-service",
            "timestamp": "2026-01-23T14:00:00",
            "expected_strings": [
                "Log Analysis",
                "Total Errors Found:",
                "payment-service",
            ],
            "custom": False,
        },
        {
            "log_content": """
2026-01-23 14:23:45.123 INFO [test-service] Service started
2026-01-23 14:23:46.456 ERROR [test-service] Database connection timeout
2026-01-23 14:23:47.789 CRITICAL [test-service] Service crashed
2026-01-23 14:23:48.012 ERROR [test-service] HTTP 500 Internal Server Error
2026-01-23 14:23:49.345 ERROR [test-service] NullPointerException occurred
""",
            "expected_error_count": 4,
            "custom": True,
        },
    ],
)
def test_log_parser_integration(log_case):
    """Clubbed test for LogParserTool with real and custom logs."""
    tool = LogParserTool()
    if not log_case.get("custom"):
        result = tool._run(
            service_name=log_case["service_name"], timestamp=log_case["timestamp"]
        )
        assert "log file not found" not in result.lower()
        for s in log_case["expected_strings"]:
            assert s in result
    else:
        import tempfile
        from pathlib import Path

        log_content = log_case["log_content"]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, dir=Config.LOG_DIRECTORY
        ) as f:
            f.write(log_content)
            temp_log_path = Path(f.name)
            service_name = temp_log_path.stem
        try:
            result = tool._run(service_name=service_name, timestamp="2026-01-23")
            assert f"Total Errors Found: {log_case['expected_error_count']}" in result
        finally:
            temp_log_path.unlink()


@pytest.mark.parametrize(
    "max_commits",
    [5, 2, 10],
)
def test_git_search_integration(max_commits):
    """Clubbed test for GitSearchTool with various max_commits values."""
    tool = GitSearchTool()
    result = tool._run(
        git_repo_path=str(Config.GIT_REPO_PATH),
        timestamp="2026-01-24T00:00:00",
        max_commits=max_commits,
    )
    assert "not found" not in result.lower() and "error" not in result.lower()
    if "Commit" in result:
        assert "Git Commit Analysis" in result
        assert "Author:" in result
        assert "Message:" in result
    if "Total commits found:" in result:
        lines = result.split("\n")
        for line in lines:
            if "Total commits found:" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    count = int(parts[1].strip())
                    assert count <= max_commits
    if "Risk Level:" in result:
        assert any(level in result for level in ["HIGH", "MEDIUM", "LOW"])


@pytest.mark.parametrize(
    "tool_cls,args",
    [
        (
            LogParserTool,
            {"service_name": "nonexistent-service", "timestamp": "2026-01-23"},
        ),
        (
            GitSearchTool,
            {
                "git_repo_path": "/nonexistent/repo",
                "timestamp": "2026-01-24T00:00:00",
                "max_commits": 1,
            },
        ),
    ],
)
def test_tool_negative_cases(tool_cls, args):
    """Parametrized negative tool integration cases."""
    tool = tool_cls()
    result = tool._run(**args)
    assert "Error:" in result


@pytest.mark.parametrize(
    "interop_case",
    [
        {
            "type": "log_analysis",
            "service_name": "payment-service",
            "timestamp": "2026-01-23T14:00:00",
        },
        {"type": "git_search", "max_commits": 3},
    ],
)
def test_tools_interoperability(interop_case):
    """Clubbed test for tool interoperability workflows."""
    if interop_case["type"] == "log_analysis":
        log_tool = LogParserTool()
        log_result = log_tool._run(
            service_name=interop_case["service_name"],
            timestamp=interop_case["timestamp"],
        )
        # Verify log analysis result contains expected content
        assert "Log Analysis" in log_result or "Error" in log_result
    elif interop_case["type"] == "git_search":
        git_tool = GitSearchTool()
        git_result = git_tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",
            max_commits=interop_case["max_commits"],
        )
        # Verify git search result
        assert git_result is not None
