"""Tests for custom tools."""

import pytest
from pathlib import Path
from src.incident_responder.tools import LogParserTool, GitSearchTool, ReportGeneratorTool
from src.incident_responder.utils.config import Config


class TestLogParserTool:
    """Tests for LogParserTool."""
    
    def test_log_parser_finds_errors(self):
        """Test that log parser correctly identifies errors."""
        tool = LogParserTool()
        result = tool._run(
            service_name="payment-service",
            timestamp="2026-01-23T14:00:00"
        )
        
        assert "payment-service" in result
        assert "Error" in result or "ERROR" in result
        assert "Total Errors Found:" in result
    
    def test_log_parser_handles_missing_file(self):
        """Test that log parser handles missing log files gracefully."""
        tool = LogParserTool()
        result = tool._run(
            service_name="nonexistent-service",
            timestamp="2026-01-23T14:00:00"
        )
        
        assert "Error" in result
        assert "not found" in result.lower()


class TestGitSearchTool:
    """Tests for GitSearchTool."""
    
    def test_git_search_finds_commits(self):
        """Test that git search finds commits."""
        tool = GitSearchTool()
        result = tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",  # After all commits
            max_commits=5
        )
        
        assert "Commit" in result
        assert "Author:" in result
        assert "Message:" in result
    
    def test_git_search_handles_invalid_repo(self):
        """Test that git search handles invalid repositories."""
        tool = GitSearchTool()
        result = tool._run(
            git_repo_path="/nonexistent/path",
            timestamp="2026-01-24T00:00:00",
            max_commits=5
        )
        
        assert "Error" in result or "not found" in result.lower()


class TestReportGeneratorTool:
    """Tests for ReportGeneratorTool."""
    
    def test_report_generator_creates_file(self):
        """Test that report generator creates a file."""
        tool = ReportGeneratorTool()
        test_content = """
# Post-Mortem Report

## Summary
Test incident report.

## Error
Database connection timeout.

## Commit
Recent config change (commit abc123).

## Recommendation
Increase timeout values.
"""
        result = tool._run(
            investigation_id="test-123",
            content=test_content
        )
        
        assert "successfully saved" in result.lower()
        assert "postmortem_test-123" in result
    
    def test_report_generator_handles_errors(self):
        """Test that report generator handles errors gracefully."""
        tool = ReportGeneratorTool()
        # Test with invalid content that might cause issues
        result = tool._run(
            investigation_id="",  # Empty ID might cause issues
            content="Test content"
        )
        
        # Should either succeed or return an error message
        assert isinstance(result, str)
