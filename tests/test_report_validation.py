"""Unit tests for report content validation (as per requirements).

Per the technical requirements:
- Report MUST contain "Error" (describing the issue)
- Report MUST contain "Commit" (referencing code changes)
- Report MUST contain "Recommendation" (prevention steps)
"""


def validate_report_content(content: str) -> tuple[bool, list[str]]:
    """
    Validate that report content contains required keywords.
    
    Returns:
        tuple: (is_valid, list of missing keywords)
    """
    required_keywords = {
        "Error": ["Error", "error", "ERROR"],
        "Commit": ["Commit", "commit", "COMMIT"],
        "Recommendation": ["Recommendation", "recommendation", "RECOMMENDATION"],
    }
    
    missing = []
    for category, variations in required_keywords.items():
        if not any(keyword in content for keyword in variations):
            missing.append(category)
    
    return len(missing) == 0, missing


class TestReportContentValidation:
    """Unit tests for report validation logic."""

    def test_validates_complete_report(self):
        """Should validate a report with all required keywords."""
        sample_content = """
# Post-Mortem Report

## Error Analysis
Database connection timeout error occurred.

## Root Cause
The recent Commit abc123 changed timeout settings.

## Recommendation
Revert the configuration change.
"""
        is_valid, missing = validate_report_content(sample_content)
        assert is_valid
        assert len(missing) == 0

    def test_detects_missing_error_keyword(self):
        """Should detect when Error keyword is missing."""
        content = """
# Post-Mortem Report
Commit abc123 was deployed.
Recommendation: Add monitoring.
"""
        is_valid, missing = validate_report_content(content)
        assert not is_valid
        assert "Error" in missing

    def test_detects_missing_commit_keyword(self):
        """Should detect when Commit keyword is missing."""
        content = """
# Post-Mortem Report
Error: Database timeout.
Recommendation: Add monitoring.
"""
        is_valid, missing = validate_report_content(content)
        assert not is_valid
        assert "Commit" in missing

    def test_detects_missing_recommendation_keyword(self):
        """Should detect when Recommendation keyword is missing."""
        content = """
# Post-Mortem Report
Error: Database timeout.
Commit abc123 was deployed.
"""
        is_valid, missing = validate_report_content(content)
        assert not is_valid
        assert "Recommendation" in missing

    def test_accepts_case_variations(self):
        """Should accept case variations of keywords."""
        content = """
error occurred
commit abc123
recommendation: fix it
"""
        is_valid, missing = validate_report_content(content)
        assert is_valid

    def test_detects_multiple_missing_keywords(self):
        """Should detect multiple missing keywords."""
        content = "Just some random text"
        is_valid, missing = validate_report_content(content)
        assert not is_valid
        assert len(missing) == 3
        assert "Error" in missing
        assert "Commit" in missing
        assert "Recommendation" in missing
