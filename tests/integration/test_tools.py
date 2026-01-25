"""Integration tests for tools working with actual files.

These tests verify that tools correctly interact with the file system
and external tools (like git).
"""

import tempfile
from pathlib import Path

from src.incident_responder.tools import (
    GitSearchTool,
    LogParserTool,
    ReportGeneratorTool,
)
from src.incident_responder.utils.config import Config


class TestLogParserIntegration:
    """Integration tests for LogParserTool with actual log files."""

    def test_parses_real_payment_service_logs(self):
        """Should parse actual payment-service logs."""
        tool = LogParserTool()
        result = tool._run(
            service_name="payment-service", timestamp="2026-01-23T14:00:00"
        )

        # Should not be an error message
        assert "log file not found" not in result.lower()

        # Should contain analysis results
        assert "Log Analysis" in result
        assert "Total Errors Found:" in result
        assert "payment-service" in result

    def test_log_parser_with_custom_log_file(self):
        """Should parse custom log file with various error types."""
        # Create a temporary log file
        log_content = """
2026-01-23 14:23:45.123 INFO [test-service] Service started
2026-01-23 14:23:46.456 ERROR [test-service] Database connection timeout
2026-01-23 14:23:47.789 CRITICAL [test-service] Service crashed
2026-01-23 14:23:48.012 ERROR [test-service] HTTP 500 Internal Server Error
2026-01-23 14:23:49.345 ERROR [test-service] NullPointerException occurred
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".log", delete=False, dir=Config.LOG_DIRECTORY
        ) as f:
            f.write(log_content)
            temp_log_path = Path(f.name)
            service_name = temp_log_path.stem

        try:
            tool = LogParserTool()
            result = tool._run(service_name=service_name, timestamp="2026-01-23")

            # Verify it found the errors
            assert "Total Errors Found: 4" in result
            assert "Database" in result
            assert "HTTP" in result or "Network" in result

        finally:
            # Cleanup
            temp_log_path.unlink()


class TestGitSearchIntegration:
    """Integration tests for GitSearchTool with actual repository."""

    def test_searches_mock_repository(self):
        """Should search the mock repository successfully."""
        tool = GitSearchTool()
        result = tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",
            max_commits=5,
        )

        # Should not be an error
        assert "not found" not in result.lower() or "Error" not in result

        # Should contain git analysis
        if "Commit" in result:
            assert "Git Commit Analysis" in result
            assert "Author:" in result
            assert "Message:" in result

    def test_git_search_respects_max_commits_limit(self):
        """Should respect the max_commits parameter."""
        tool = GitSearchTool()

        # Search with limit of 2
        result = tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",
            max_commits=2,
        )

        # If commits are found, should not exceed limit
        if "Total commits found:" in result:
            # Extract the number (simple parsing)
            lines = result.split("\n")
            for line in lines:
                if "Total commits found:" in line:
                    # Parse the number
                    parts = line.split(":")
                    if len(parts) > 1:
                        count = int(parts[1].strip())
                        assert count <= 2

    def test_git_search_risk_assessment(self):
        """Should assess risk levels of commits."""
        tool = GitSearchTool()
        result = tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",
            max_commits=10,
        )

        if "Risk Level:" in result:
            # Should contain one of the risk levels
            assert "HIGH" in result or "MEDIUM" in result or "LOW" in result


class TestReportGeneratorIntegration:
    """Integration tests for ReportGeneratorTool with file system."""

    def test_generates_and_saves_report(self):
        """Should generate and save a complete report."""
        tool = ReportGeneratorTool()
        test_id = "integration-test-001"
        content = """
# Post-Mortem Report

## Summary
Test incident in payment-service.

## Timeline
- 14:23:45 - Error detected

## Root Cause
Database timeout

## Recommendations
1. Increase timeout
2. Add monitoring
"""
        result = tool._run(investigation_id=test_id, content=content)

        # Should succeed
        assert "successfully saved" in result.lower()
        assert test_id in result

        # Verify file was created
        report_files = list(Config.REPORTS_DIRECTORY.glob(f"postmortem_{test_id}_*"))
        assert len(report_files) > 0

        # Verify content
        report_content = report_files[0].read_text()
        assert "Post-Mortem Report" in report_content
        assert "Timeline" in report_content
        assert test_id in report_content

        # Cleanup
        for report_file in report_files:
            report_file.unlink()

    def test_report_includes_metadata(self):
        """Should include metadata in generated report."""
        tool = ReportGeneratorTool()
        test_id = "integration-test-002"
        content = "# Simple Report"

        result = tool._run(investigation_id=test_id, content=content)
        assert "successfully" in result.lower()

        # Find and verify the report
        report_files = list(Config.REPORTS_DIRECTORY.glob(f"postmortem_{test_id}_*"))
        assert len(report_files) > 0

        report_content = report_files[0].read_text()

        # Verify metadata
        assert "---" in report_content
        assert f"Investigation ID: {test_id}" in report_content
        assert "Generated:" in report_content

        # Cleanup
        for report_file in report_files:
            report_file.unlink()

    def test_multiple_reports_same_id_different_timestamps(self):
        """Should generate multiple reports with different timestamps."""
        tool = ReportGeneratorTool()
        test_id = "integration-test-003"
        content = "# Report Content"

        # Generate first report
        result1 = tool._run(investigation_id=test_id, content=content)
        assert "successfully" in result1.lower()

        # Small delay to ensure different timestamp
        import time

        time.sleep(1)

        # Generate second report with same ID
        result2 = tool._run(investigation_id=test_id, content=content)
        assert "successfully" in result2.lower()

        # Verify both files exist
        report_files = list(Config.REPORTS_DIRECTORY.glob(f"postmortem_{test_id}_*"))
        assert len(report_files) >= 2

        # Cleanup
        for report_file in report_files:
            report_file.unlink()


class TestToolsInteroperability:
    """Test that tools work together in a workflow."""

    def test_log_parser_and_report_generator_workflow(self):
        """Test workflow: parse logs -> generate report."""
        # 1. Parse logs
        log_tool = LogParserTool()
        log_result = log_tool._run(
            service_name="payment-service", timestamp="2026-01-23T14:00:00"
        )

        # 2. Use log analysis in report
        report_tool = ReportGeneratorTool()
        report_content = f"""
# Post-Mortem Report

## Log Analysis
{log_result}

## Conclusion
Based on log analysis above.
"""
        test_id = "workflow-test-001"
        report_result = report_tool._run(
            investigation_id=test_id, content=report_content
        )

        assert "successfully" in report_result.lower()

        # Verify report contains log analysis
        report_files = list(Config.REPORTS_DIRECTORY.glob(f"postmortem_{test_id}_*"))
        if report_files:
            content = report_files[0].read_text()
            assert "Log Analysis" in content

            # Cleanup
            for report_file in report_files:
                report_file.unlink()

    def test_git_search_and_report_generator_workflow(self):
        """Test workflow: search git -> generate report."""
        # 1. Search git commits
        git_tool = GitSearchTool()
        git_result = git_tool._run(
            git_repo_path=str(Config.GIT_REPO_PATH),
            timestamp="2026-01-24T00:00:00",
            max_commits=3,
        )

        # 2. Use git analysis in report
        report_tool = ReportGeneratorTool()
        report_content = f"""
# Post-Mortem Report

## Git Commits
{git_result}

## Analysis
Recent commits analyzed.
"""
        test_id = "workflow-test-002"
        report_result = report_tool._run(
            investigation_id=test_id, content=report_content
        )

        assert "successfully" in report_result.lower()

        # Cleanup
        report_files = list(Config.REPORTS_DIRECTORY.glob(f"postmortem_{test_id}_*"))
        for report_file in report_files:
            report_file.unlink()
