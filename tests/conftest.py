"""Pytest configuration and fixtures."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        log_content = """
2026-01-23 14:23:45.123 INFO [test-service] Service started
2026-01-23 14:23:46.456 ERROR [test-service] Database connection timeout
2026-01-23 14:23:47.789 CRITICAL [test-service] Service crashed
2026-01-23 14:23:48.012 INFO [test-service] Service restarted
"""
        f.write(log_content)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_report_dir():
    """Create a temporary directory for reports."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_investigation_payload():
    """Sample investigation request payload."""
    return {
        "service_name": "payment-service",
        "alert_type": "database_timeout",
        "timestamp": "2026-01-23T14:23:45.123",
    }


@pytest.fixture
def sample_log_content():
    """Sample log content for testing."""
    return """
2026-01-23 14:23:45.123 INFO [payment-service] Processing payment request
2026-01-23 14:23:46.456 ERROR [payment-service] Database connection timeout after 30s
2026-01-23 14:23:47.789 CRITICAL [payment-service] Unable to process payment
2026-01-23 14:23:48.012 ERROR [payment-service] Transaction rollback failed
2026-01-23 14:23:49.345 INFO [payment-service] Attempting reconnection
"""


@pytest.fixture
def sample_report_content():
    """Sample report content for testing."""
    return """
# Post-Mortem Report

## Executive Summary
Database timeout incident in payment-service.

## Timeline
- **14:23:45** - Service processing payment
- **14:23:46** - Database connection timeout
- **14:23:47** - Service unable to process
- **14:23:48** - Transaction rollback failed

## Root Cause Analysis
The database connection timeout was caused by:
1. Recent commit reducing timeout from 30s to 5s
2. Increased database load during peak hours

## Impact
- 15 failed payment transactions
- Service degradation for 2 minutes

## Resolution
- Reverted timeout configuration
- Service automatically recovered

## Recommendations
1. Implement gradual rollout for configuration changes
2. Add database connection monitoring
3. Set up alerts for timeout errors
4. Review timeout values under load testing
"""


@pytest.fixture
def mock_git_commits():
    """Mock git commit data for testing."""
    return [
        {
            "hash": "9f6d43b2",
            "author": "John Doe",
            "date": "2026-01-23 14:00:00",
            "message": "Reduce database timeout to improve performance",
            "files_changed": ["config/database.yaml", "src/database.py"],
            "risk_level": "HIGH",
        },
        {
            "hash": "a1b2c3d4",
            "author": "Jane Smith",
            "date": "2026-01-23 10:00:00",
            "message": "Update payment processing logic",
            "files_changed": ["src/payment_processor.py"],
            "risk_level": "MEDIUM",
        },
        {
            "hash": "e5f6g7h8",
            "author": "Bob Wilson",
            "date": "2026-01-22 15:00:00",
            "message": "Update README documentation",
            "files_changed": ["README.md"],
            "risk_level": "LOW",
        },
    ]


@pytest.fixture(autouse=True)
def reset_investigation_storage():
    """Reset in-memory investigation storage before each test."""
    from src.incident_responder.api.routes import investigations

    investigations.clear()
    yield
    investigations.clear()
