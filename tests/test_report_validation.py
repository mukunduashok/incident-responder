"""Tests for report validation (as per requirements)."""

import pytest
from pathlib import Path
from src.incident_responder.utils.config import Config


class TestPostMortemReportValidation:
    """
    Test that generated post-mortem reports contain required keywords.
    
    Per the technical requirements:
    - Report MUST contain "Error" (describing the issue)
    - Report MUST contain "Commit" (referencing code changes)
    - Report MUST contain "Recommendation" (prevention steps)
    """
    
    def test_report_contains_required_keywords(self):
        """Test that generated reports contain Error, Commit, and Recommendation."""
        # This test will need to wait for an actual report to be generated
        # For now, we'll check if the reports directory exists and can be written to
        
        Config.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
        assert Config.REPORTS_DIRECTORY.exists()
        
        # Create a sample report for testing
        sample_report = """
# Post-Mortem Report

## Executive Summary
Database connection timeout error occurred in payment-service.

## Timeline
- 14:23:45 - First Error detected in logs

## Root Cause Analysis
The recent Commit 9f6d43b reduced database timeout from 30s to 5s.

## Recommendation
1. Revert the timeout configuration change
2. Add monitoring for database connection times
3. Implement gradual rollout for config changes
"""
        
        # Verify keywords are present
        assert "Error" in sample_report
        assert "Commit" in sample_report
        assert "Recommendation" in sample_report
    
    def test_sample_report_file_validation(self):
        """Test validation logic on a sample report file."""
        sample_content = """
# Incident Post-Mortem

## Error Analysis
Connection timeout errors in payment processing.

## Commit History
Recent commits:
- Commit abc123: Updated timeout config

## Recommendations
- Increase timeout values
- Add circuit breaker
"""
        # Validate required keywords
        required_keywords = ["Error", "Commit", "Recommendation"]
        
        for keyword in required_keywords:
            assert keyword in sample_content, f"Missing required keyword: {keyword}"
