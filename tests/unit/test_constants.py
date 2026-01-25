"""Unit tests for constants module."""

from src.incident_responder.constants import (
    API_PREFIX,
    API_VERSION,
    DEFAULT_MAX_COMMITS,
    ERROR_LEVELS,
    GIT_SHORT_HASH_LENGTH,
    HIGH_RISK_PATTERNS,
    LLM_TEMPERATURE,
    LOG_LEVEL_ERROR,
    MAX_ERROR_MESSAGE_LENGTH,
    MAX_FILES_TO_DISPLAY,
    MAX_SAMPLE_ERRORS,
    MEDIUM_RISK_PATTERNS,
    REPORT_FILENAME_EXTENSION,
    REPORT_FILENAME_PREFIX,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
)


class TestAPIConstants:
    """Test API-related constants."""

    def test_api_version_format(self):
        """API version should follow semantic versioning."""
        assert isinstance(API_VERSION, str)
        assert "." in API_VERSION
        parts = API_VERSION.split(".")
        assert len(parts) >= 2

    def test_api_prefix_starts_with_slash(self):
        """API prefix should start with a slash."""
        assert API_PREFIX.startswith("/")


class TestLLMConstants:
    """Test LLM-related constants."""

    def test_llm_temperature_in_valid_range(self):
        """LLM temperature should be between 0 and 2 for determinism."""
        assert 0 <= LLM_TEMPERATURE < 0.5  # Low for deterministic outputs


class TestGitConstants:
    """Test Git-related constants."""

    def test_git_constants_have_valid_ranges(self):
        """Git-related constants should be in valid ranges."""
        assert DEFAULT_MAX_COMMITS > 0
        assert 4 <= GIT_SHORT_HASH_LENGTH <= 40
        assert 1 <= MAX_FILES_TO_DISPLAY <= 20

    def test_risk_levels_are_unique(self):
        """Risk levels should be unique strings."""
        risk_levels = {RISK_LEVEL_HIGH, RISK_LEVEL_MEDIUM, RISK_LEVEL_LOW}
        assert len(risk_levels) == 3

    def test_risk_patterns_defined(self):
        """High and medium risk patterns should be defined."""
        assert len(HIGH_RISK_PATTERNS) > 0
        assert len(MEDIUM_RISK_PATTERNS) > 0


class TestLogParsingConstants:
    """Test log parsing-related constants."""

    def test_error_levels_configured(self):
        """Error levels should include ERROR and not be empty."""
        assert len(ERROR_LEVELS) > 0
        assert LOG_LEVEL_ERROR in ERROR_LEVELS

    def test_parsing_limits_are_reasonable(self):
        """Parsing limits should be in reasonable ranges."""
        assert 5 <= MAX_SAMPLE_ERRORS <= 100
        assert 50 <= MAX_ERROR_MESSAGE_LENGTH <= 1000


class TestReportConstants:
    """Test report generation constants."""

    def test_report_filename_format(self):
        """Report filename should have valid prefix and markdown extension."""
        assert len(REPORT_FILENAME_PREFIX) > 0
        assert REPORT_FILENAME_EXTENSION == ".md"


class TestStatusConstants:
    """Test investigation status constants."""

    def test_status_values_are_valid(self):
        """All status values should be unique and lowercase."""
        statuses = {STATUS_PENDING, STATUS_RUNNING, STATUS_COMPLETED, STATUS_FAILED}
        assert len(statuses) == 4
        assert all(status.islower() for status in statuses)
