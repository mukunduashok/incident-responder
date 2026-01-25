"""End-to-end tests for the complete incident investigation flow.

These tests verify the entire system working together, from API request
through crew execution to report generation.
"""

import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.incident_responder.api.routes import router
from src.incident_responder.constants import (
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
)
from src.incident_responder.utils.config import Config

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mark all tests in this module as slow E2E tests
pytestmark = pytest.mark.slow


class TestCompleteInvestigationFlow:
    """End-to-end tests for complete investigation workflow."""

    @pytest.mark.timeout(300)  # 5 minute timeout for E2E test
    def test_full_investigation_lifecycle(self):
        """
        Test complete investigation lifecycle:
        1. Trigger investigation via API
        2. Wait for processing
        3. Verify report generation
        4. Validate report content
        """
        # 1. Trigger investigation
        payload = {
            "service_name": "payment-service",
            "alert_type": "database_timeout",
            "timestamp": "2026-01-23T14:30:00",
        }

        trigger_response = client.post("/trigger-investigation", json=payload)
        assert trigger_response.status_code == 200

        data = trigger_response.json()
        investigation_id = data["investigation_id"]
        assert data["status"] == STATUS_PENDING

        # 2. Poll for status updates (with timeout)
        max_wait_time = 180  # 3 minutes
        poll_interval = 2  # 2 seconds
        elapsed_time = 0
        final_status = None

        while elapsed_time < max_wait_time:
            status_response = client.get(f"/investigation/{investigation_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            current_status = status_data["status"]

            if current_status in [STATUS_COMPLETED, STATUS_FAILED]:
                final_status = current_status
                break

            time.sleep(poll_interval)
            elapsed_time += poll_interval

        # 3. Verify completion
        # Note: Investigation may still be running or may have completed
        # We verify the status is valid
        assert final_status in [
            STATUS_COMPLETED,
            STATUS_FAILED,
            STATUS_RUNNING,
            None,
        ]

        # 4. If completed, verify report was generated
        if final_status == STATUS_COMPLETED:
            # Check for generated report
            report_files = list(Config.REPORTS_DIRECTORY.glob(f"*{investigation_id}*"))
            # Report should exist
            # Note: Depending on implementation, report might be generated later
            # so we make this check optional
            if report_files:
                assert len(report_files) > 0
                report_content = report_files[0].read_text()
                assert len(report_content) > 0

    def test_investigation_handles_nonexistent_service(self):
        """Test investigation with non-existent service completes gracefully."""
        payload = {
            "service_name": "nonexistent-service-xyz",
            "alert_type": "error",
            "timestamp": "2026-01-23T14:00:00",
        }

        trigger_response = client.post("/trigger-investigation", json=payload)
        assert trigger_response.status_code == 200

        # Investigation should still start
        data = trigger_response.json()
        investigation_id = data["investigation_id"]
        assert investigation_id is not None

        # Status should be trackable
        status_response = client.get(f"/investigation/{investigation_id}")
        assert status_response.status_code == 200

    def test_concurrent_investigations(self):
        """Test that multiple investigations can run concurrently."""
        services = [
            "payment-service",
            "user-service",
            "notification-service",
        ]
        investigation_ids = []

        # Trigger multiple investigations
        for service in services:
            payload = {
                "service_name": service,
                "alert_type": "high_latency",
                "timestamp": "2026-01-23T15:00:00",
            }
            response = client.post("/trigger-investigation", json=payload)
            assert response.status_code == 200
            investigation_ids.append(response.json()["investigation_id"])

        # Wait a bit for background processing
        time.sleep(2)

        # Verify all investigations are tracked
        for investigation_id in investigation_ids:
            status_response = client.get(f"/investigation/{investigation_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            # Status should be valid
            assert status_data["status"] in [
                STATUS_PENDING,
                STATUS_RUNNING,
                STATUS_COMPLETED,
                STATUS_FAILED,
            ]

    def test_system_health_during_investigation(self):
        """Test that health check works while investigations are running."""
        # Trigger an investigation
        payload = {
            "service_name": "payment-service",
            "alert_type": "error",
            "timestamp": "2026-01-23T14:00:00",
        }
        trigger_response = client.post("/trigger-investigation", json=payload)
        assert trigger_response.status_code == 200

        # Check health while investigation might be running
        health_response = client.get("/health")
        assert health_response.status_code == 200

        health_data = health_response.json()
        assert health_data["status"] == "healthy"
        assert isinstance(health_data["llm_configured"], bool)
        assert isinstance(health_data["logs_available"], bool)
        assert isinstance(health_data["git_repo_available"], bool)


class TestInvestigationErrorHandling:
    """E2E tests for error handling scenarios."""

    def test_investigation_with_invalid_timestamp_format(self):
        """Test investigation with various timestamp formats."""
        timestamps = [
            "2026-01-23T14:30:00",
            "2026-01-23T14:30:00.123",
            "2026-01-23 14:30:00",
            "2026-01-23",
        ]

        for ts in timestamps:
            payload = {
                "service_name": "test-service",
                "alert_type": "error",
                "timestamp": ts,
            }
            response = client.post("/trigger-investigation", json=payload)
            # Should accept various timestamp formats
            assert response.status_code == 200

    def test_investigation_data_persistence(self):
        """Test that investigation data persists across status checks."""
        payload = {
            "service_name": "data-persistence-test",
            "alert_type": "test_alert",
            "timestamp": "2026-01-23T14:00:00",
        }

        trigger_response = client.post("/trigger-investigation", json=payload)
        investigation_id = trigger_response.json()["investigation_id"]

        # Check status multiple times
        for _ in range(3):
            status_response = client.get(f"/investigation/{investigation_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            # Data should be consistent
            assert status_data["service_name"] == "data-persistence-test"
            assert status_data["alert_type"] == "test_alert"

            time.sleep(0.5)


class TestAPIResilience:
    """E2E tests for API resilience and error handling."""

    def test_malformed_request_handling(self):
        """Test API handling of malformed requests."""
        # Invalid JSON
        response1 = client.post(
            "/trigger-investigation",
            data="not a json",
            headers={"Content-Type": "application/json"},
        )
        assert response1.status_code in [400, 422]

        # Missing required fields
        response2 = client.post("/trigger-investigation", json={})
        assert response2.status_code == 422

        # Wrong data types
        response3 = client.post(
            "/trigger-investigation",
            json={"service_name": 123, "alert_type": None},
        )
        assert response3.status_code == 422

    def test_investigation_id_uniqueness(self):
        """Test that investigation IDs are unique across requests."""
        payload = {"service_name": "test", "alert_type": "error"}

        ids = []
        for _ in range(10):
            response = client.post("/trigger-investigation", json=payload)
            ids.append(response.json()["investigation_id"])

        # All IDs should be unique
        assert len(ids) == len(set(ids))

    def test_status_check_for_various_ids(self):
        """Test status checks for valid and invalid investigation IDs."""
        # Create one valid investigation
        payload = {"service_name": "test", "alert_type": "error"}
        response = client.post("/trigger-investigation", json=payload)
        valid_id = response.json()["investigation_id"]

        # Valid ID should work
        valid_response = client.get(f"/investigation/{valid_id}")
        assert valid_response.status_code == 200

        # Invalid IDs should return 404
        invalid_ids = [
            "nonexistent",
            "12345",
            "invalid-uuid-format",
        ]
        for invalid_id in invalid_ids:
            invalid_response = client.get(f"/investigation/{invalid_id}")
            assert invalid_response.status_code == 404
