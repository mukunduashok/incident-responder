"""Unit tests for log parsing utilities."""

from src.incident_responder.constants import (
    ERROR_CATEGORY_DATABASE,
    ERROR_CATEGORY_GENERAL,
    ERROR_CATEGORY_HTTP,
    ERROR_CATEGORY_NULL_POINTER,
    ERROR_CATEGORY_STACK_TRACE,
    MAX_SAMPLE_ERRORS,
)
from src.incident_responder.utils.log_utils import (
    LogEntry,
    LogPatterns,
    categorize_error,
    extract_errors_from_logs,
    parse_log_line,
)


class TestLogEntry:
    """Test LogEntry dataclass."""

    def test_creates_log_entry(self):
        """Should create a LogEntry with all fields."""
        entry = LogEntry(
            timestamp="2026-01-23 14:23:45.123",
            level="ERROR",
            service="payment-service",
            message="Database connection timeout",
            raw_line="2026-01-23 14:23:45.123 ERROR [payment-service] Database connection timeout",
        )
        assert entry.timestamp == "2026-01-23 14:23:45.123"
        assert entry.level == "ERROR"
        assert entry.service == "payment-service"
        assert entry.message == "Database connection timeout"


class TestLogPatterns:
    """Test LogPatterns regex patterns."""

    def test_standard_log_pattern_matches_valid_log(self):
        """Should match standard log format."""
        log_line = "2026-01-23 14:23:45.123 ERROR [payment-service] Database timeout"
        match = LogPatterns.STANDARD_LOG.match(log_line)
        assert match is not None
        assert match.group("timestamp") == "2026-01-23 14:23:45.123"
        assert match.group("level") == "ERROR"
        assert match.group("service") == "payment-service"
        assert match.group("message") == "Database timeout"

    def test_standard_log_pattern_matches_different_levels(self):
        """Should match different log levels."""
        levels = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]
        for level in levels:
            log_line = f"2026-01-23 14:23:45 {level} [test-service] Test message"
            match = LogPatterns.STANDARD_LOG.match(log_line)
            assert match is not None, f"Failed to match {level}"
            assert match.group("level") == level

    def test_standard_log_pattern_handles_microseconds(self):
        """Should handle timestamps with microseconds."""
        log_line = "2026-01-23 14:23:45.123456 ERROR [service] Message"
        match = LogPatterns.STANDARD_LOG.match(log_line)
        assert match is not None
        assert "123456" in match.group("timestamp")

    def test_standard_log_pattern_handles_no_microseconds(self):
        """Should handle timestamps without microseconds."""
        log_line = "2026-01-23 14:23:45 ERROR [service] Message"
        match = LogPatterns.STANDARD_LOG.match(log_line)
        assert match is not None

    def test_error_keywords_pattern_matches_errors(self):
        """Should match error keywords case-insensitively."""
        keywords = ["error", "ERROR", "Exception", "FAILED", "timeout", "CRASHED"]
        for keyword in keywords:
            assert LogPatterns.ERROR_KEYWORDS.search(keyword) is not None

    def test_database_error_pattern_matches_db_errors(self):
        """Should match database-related errors."""
        db_errors = [
            "database connection failed",
            "SQL syntax error",
            "PostgreSQL timeout",
            "MySQL connection refused",
            "MongoDB replica set error",
        ]
        for error in db_errors:
            assert LogPatterns.DATABASE_ERROR.search(error) is not None

    def test_http_error_pattern_matches_http_errors(self):
        """Should match HTTP-related errors."""
        http_errors = [
            "HTTP 500 Internal Server Error",
            "status code 404",
            "connection refused on port 8080",
            "timeout on request",
        ]
        for error in http_errors:
            assert LogPatterns.HTTP_ERROR.search(error) is not None

    def test_null_pointer_pattern_matches_null_errors(self):
        """Should match null pointer and attribute errors."""
        null_errors = [
            "null pointer exception",
            "NoneType has no attribute",
            "AttributeError: 'NoneType'",
            "KeyError: 'missing_key'",
        ]
        for error in null_errors:
            assert LogPatterns.NULL_POINTER.search(error) is not None

    def test_stack_trace_pattern_matches_traces(self):
        """Should match stack traces."""
        traces = [
            "Traceback (most recent call last):",
            "Stack trace:",
            "  at module.function (file.py:123)",
            '  File "script.py", line 42',
        ]
        for trace in traces:
            assert LogPatterns.STACK_TRACE.search(trace) is not None


class TestParseLogLine:
    """Test parse_log_line function."""

    def test_parses_valid_log_line(self):
        """Should parse a valid log line."""
        log_line = "2026-01-23 14:23:45.123 ERROR [payment-service] Connection timeout"
        entry = parse_log_line(log_line)
        assert entry is not None
        assert entry.timestamp == "2026-01-23 14:23:45.123"
        assert entry.level == "ERROR"
        assert entry.service == "payment-service"
        assert entry.message == "Connection timeout"

    def test_returns_none_for_invalid_line(self):
        """Should return None for invalid log lines."""
        invalid_lines = [
            "This is not a log line",
            "ERROR: Missing timestamp",
            "2026-01-23 INVALID [service] message",
        ]
        for line in invalid_lines:
            entry = parse_log_line(line)
            assert entry is None

    def test_handles_multiline_messages(self):
        """Should capture the first line of multiline messages."""
        log_line = "2026-01-23 14:23:45 ERROR [service] Error occurred"
        entry = parse_log_line(log_line)
        assert entry is not None
        assert entry.message == "Error occurred"

    def test_preserves_raw_line(self):
        """Should preserve the raw log line."""
        log_line = "2026-01-23 14:23:45 ERROR [service] Test"
        entry = parse_log_line(log_line)
        assert entry is not None
        assert entry.raw_line == log_line


class TestCategorizeError:
    """Test categorize_error function."""

    def test_categorizes_database_errors(self):
        """Should categorize database errors."""
        message = "PostgreSQL connection timeout occurred"
        categories = categorize_error(message)
        assert ERROR_CATEGORY_DATABASE in categories

    def test_categorizes_http_errors(self):
        """Should categorize HTTP errors."""
        message = "HTTP 500 Internal Server Error"
        categories = categorize_error(message)
        assert ERROR_CATEGORY_HTTP in categories

    def test_categorizes_null_pointer_errors(self):
        """Should categorize null pointer errors."""
        message = "AttributeError: 'NoneType' object has no attribute 'value'"
        categories = categorize_error(message)
        assert ERROR_CATEGORY_NULL_POINTER in categories

    def test_categorizes_stack_traces(self):
        """Should categorize stack traces."""
        message = "Traceback (most recent call last): ..."
        categories = categorize_error(message)
        assert ERROR_CATEGORY_STACK_TRACE in categories

    def test_categorizes_multiple_types(self):
        """Should categorize errors with multiple types."""
        message = "Database connection failed with HTTP 500"
        categories = categorize_error(message)
        assert ERROR_CATEGORY_DATABASE in categories
        assert ERROR_CATEGORY_HTTP in categories

    def test_returns_general_for_uncategorized(self):
        """Should return General for uncategorized errors."""
        message = "Some random error message"
        categories = categorize_error(message)
        assert ERROR_CATEGORY_GENERAL in categories

    def test_returns_list(self):
        """Should always return a list."""
        message = "Any error message"
        categories = categorize_error(message)
        assert isinstance(categories, list)
        assert len(categories) > 0


class TestExtractErrorsFromLogs:
    """Test extract_errors_from_logs function."""

    def test_extracts_errors_from_log_content(self):
        """Should extract errors from log content."""
        log_content = """
2026-01-23 14:23:45 INFO [payment-service] Starting service
2026-01-23 14:23:46 ERROR [payment-service] Database connection failed
2026-01-23 14:23:47 CRITICAL [payment-service] Service crashed
2026-01-23 14:23:48 INFO [payment-service] Attempting restart
"""
        result = extract_errors_from_logs(log_content)
        assert result["total_errors"] == 2
        assert len(result["sample_errors"]) == 2

    def test_counts_error_types(self):
        """Should count different error types."""
        log_content = """
2026-01-23 14:23:45 ERROR [service] Database timeout
2026-01-23 14:23:46 ERROR [service] HTTP 500 error
2026-01-23 14:23:47 ERROR [service] Another database error
"""
        result = extract_errors_from_logs(log_content)
        assert ERROR_CATEGORY_DATABASE in result["error_types"]
        assert ERROR_CATEGORY_HTTP in result["error_types"]

    def test_tracks_first_error_timestamp(self):
        """Should track the timestamp of the first error."""
        log_content = """
2026-01-23 14:23:45 INFO [service] Starting
2026-01-23 14:23:46 ERROR [service] First error
2026-01-23 14:23:47 ERROR [service] Second error
"""
        result = extract_errors_from_logs(log_content)
        assert result["first_error_timestamp"] == "2026-01-23 14:23:46"

    def test_identifies_affected_services(self):
        """Should identify all affected services."""
        log_content = """
2026-01-23 14:23:45 ERROR [payment-service] Error 1
2026-01-23 14:23:46 ERROR [user-service] Error 2
2026-01-23 14:23:47 ERROR [payment-service] Error 3
"""
        result = extract_errors_from_logs(log_content)
        affected = result["affected_services"]
        assert "payment-service" in affected
        assert "user-service" in affected
        assert len(affected) == 2

    def test_limits_sample_errors(self):
        """Should limit sample errors to MAX_SAMPLE_ERRORS."""
        # Create log with more than MAX_SAMPLE_ERRORS errors
        error_lines = [
            f"2026-01-23 14:23:{i:02d} ERROR [service] Error {i}"
            for i in range(MAX_SAMPLE_ERRORS + 5)
        ]
        log_content = "\n".join(error_lines)
        result = extract_errors_from_logs(log_content)
        assert len(result["sample_errors"]) == MAX_SAMPLE_ERRORS

    def test_handles_empty_log(self):
        """Should handle empty log content."""
        result = extract_errors_from_logs("")
        assert result["total_errors"] == 0
        assert result["first_error_timestamp"] is None
        assert len(result["affected_services"]) == 0

    def test_handles_log_with_no_errors(self):
        """Should handle logs with no errors."""
        log_content = """
2026-01-23 14:23:45 INFO [service] Starting
2026-01-23 14:23:46 DEBUG [service] Debug message
2026-01-23 14:23:47 INFO [service] Processing complete
"""
        result = extract_errors_from_logs(log_content)
        assert result["total_errors"] == 0
        assert result["first_error_timestamp"] is None

    def test_includes_critical_and_fatal_levels(self):
        """Should include CRITICAL and FATAL level logs as errors."""
        log_content = """
2026-01-23 14:23:45 CRITICAL [service] Critical error
2026-01-23 14:23:46 FATAL [service] Fatal error
2026-01-23 14:23:47 ERROR [service] Regular error
"""
        result = extract_errors_from_logs(log_content)
        assert result["total_errors"] == 3
