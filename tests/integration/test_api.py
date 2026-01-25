"""Integration tests for API endpoints.

These tests verify that multiple components work together correctly,
including routes, models, and background tasks.
"""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.incident_responder.api.routes import router
from src.incident_responder.constants import (
    HTTP_STATUS_NOT_FOUND,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_RUNNING,
)

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestHealthEndpointIntegration:
    """Integration tests for health check endpoint."""

    def test_health_check_returns_valid_response(self):
        """Health check should return valid JSON response with all fields."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "llm_configured" in data
        assert "logs_available" in data
        assert "git_repo_available" in data
        assert "timestamp" in data

        # Verify types
        assert isinstance(data["status"], str)
        assert isinstance(data["llm_configured"], bool)
        assert isinstance(data["logs_available"], bool)
        assert isinstance(data["git_repo_available"], bool)
        assert isinstance(data["timestamp"], str)

    def test_health_check_timestamp_format(self):
        """Health check timestamp should be in ISO format."""
        response = client.get("/health")
        data = response.json()
        timestamp = data["timestamp"]

        # Should contain T separator for ISO format
        assert "T" in timestamp or " " in timestamp
        # Should contain time components
        assert ":" in timestamp


class TestInvestigationWorkflowIntegration:
    """Integration tests for investigation workflow."""

    def test_complete_investigation_workflow(self):
        """Test complete workflow: trigger -> check status -> wait for completion."""
        # 1. Trigger investigation
        payload = {
            "service_name": "payment-service",
            "alert_type": "database_timeout",
            "timestamp": "2026-01-23T14:23:45.123",
        }
        trigger_response = client.post("/trigger-investigation", json=payload)
        assert trigger_response.status_code == 200

        trigger_data = trigger_response.json()
        investigation_id = trigger_data["investigation_id"]

        # Verify trigger response
        assert investigation_id is not None
        assert trigger_data["status"] == STATUS_PENDING
        assert "started_at" in trigger_data
        assert "report_path" in trigger_data

        # 2. Check initial status
        status_response = client.get(f"/investigation/{investigation_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["service_name"] == "payment-service"
        assert status_data["alert_type"] == "database_timeout"
        assert status_data["status"] in [
            STATUS_PENDING,
            STATUS_RUNNING,
            STATUS_COMPLETED,
            STATUS_FAILED,
        ]

    def test_investigation_with_default_timestamp(self):
        """Test investigation with auto-generated timestamp."""
        payload = {"service_name": "user-service", "alert_type": "high_latency"}

        response = client.post("/trigger-investigation", json=payload)
        assert response.status_code == 200

        data = response.json()
        investigation_id = data["investigation_id"]

        # Get status to verify timestamp was auto-generated
        status_response = client.get(f"/investigation/{investigation_id}")
        status_data = status_response.json()
        assert "timestamp" in status_data
        assert status_data["timestamp"] is not None

    def test_multiple_concurrent_investigations(self):
        """Test that multiple investigations can run concurrently."""
        services = ["service-1", "service-2", "service-3"]
        investigation_ids = []

        # Trigger multiple investigations
        for service in services:
            payload = {"service_name": service, "alert_type": "error"}
            response = client.post("/trigger-investigation", json=payload)
            assert response.status_code == 200
            investigation_ids.append(response.json()["investigation_id"])

        # Verify all investigations are tracked
        for investigation_id in investigation_ids:
            status_response = client.get(f"/investigation/{investigation_id}")
            assert status_response.status_code == 200

        # Verify all IDs are unique
        assert len(set(investigation_ids)) == len(investigation_ids)

    def test_investigation_id_is_valid_uuid(self):
        """Investigation ID should be a valid UUID."""
        payload = {"service_name": "test-service", "alert_type": "error"}
        response = client.post("/trigger-investigation", json=payload)
        investigation_id = response.json()["investigation_id"]

        # Should be parseable as UUID
        try:
            uuid.UUID(investigation_id)
        except ValueError:
            pytest.fail(f"Investigation ID {investigation_id} is not a valid UUID")

    def test_get_nonexistent_investigation(self):
        """Getting nonexistent investigation should return 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/investigation/{fake_id}")
        assert response.status_code == HTTP_STATUS_NOT_FOUND

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_investigation_validation_errors(self):
        """Test various validation error scenarios."""
        # Missing service_name
        response1 = client.post("/trigger-investigation", json={"alert_type": "error"})
        assert response1.status_code == 422

        # Missing alert_type
        response2 = client.post("/trigger-investigation", json={"service_name": "test"})
        assert response2.status_code == 422

        # Empty payload
        response3 = client.post("/trigger-investigation", json={})
        assert response3.status_code == 422

        # Invalid JSON
        response4 = client.post(
            "/trigger-investigation",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response4.status_code == 422

    def test_investigation_preserves_input_data(self):
        """Investigation should preserve input data in status."""
        payload = {
            "service_name": "payment-processor",
            "alert_type": "timeout_error",
            "timestamp": "2026-01-25T10:30:00.000",
        }

        trigger_response = client.post("/trigger-investigation", json=payload)
        investigation_id = trigger_response.json()["investigation_id"]

        status_response = client.get(f"/investigation/{investigation_id}")
        status_data = status_response.json()

        assert status_data["service_name"] == payload["service_name"]
        assert status_data["alert_type"] == payload["alert_type"]
        assert status_data["timestamp"] == payload["timestamp"]

    def test_investigation_tracks_start_time(self):
        """Investigation should track when it started."""
        payload = {"service_name": "test-service", "alert_type": "error"}

        response = client.post("/trigger-investigation", json=payload)

        data = response.json()
        assert "started_at" in data

        # Started_at should be a recent timestamp
        started_at = data["started_at"]
        assert isinstance(started_at, str)
        assert len(started_at) > 0


class TestAPIResponseFormats:
    """Test API response format consistency."""

    def test_health_endpoint_response_format(self):
        """Health endpoint response should match HealthResponse model."""
        response = client.get("/health")
        data = response.json()

        required_fields = [
            "status",
            "llm_configured",
            "logs_available",
            "git_repo_available",
            "timestamp",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_trigger_investigation_response_format(self):
        """Trigger investigation response should match InvestigationResponse model."""
        payload = {"service_name": "test", "alert_type": "error"}
        response = client.post("/trigger-investigation", json=payload)
        data = response.json()

        required_fields = [
            "investigation_id",
            "status",
            "message",
            "started_at",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_get_investigation_response_format(self):
        """Get investigation response should have expected structure."""
        # First create an investigation
        payload = {"service_name": "test", "alert_type": "error"}
        trigger_response = client.post("/trigger-investigation", json=payload)
        investigation_id = trigger_response.json()["investigation_id"]

        # Get its status
        status_response = client.get(f"/investigation/{investigation_id}")
        data = status_response.json()

        required_fields = [
            "status",
            "service_name",
            "alert_type",
            "timestamp",
            "started_at",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_error_response_format(self):
        """Error responses should have consistent format."""
        # Trigger a 404 error
        response = client.get("/investigation/nonexistent-id")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

        # Trigger a validation error
        response2 = client.post("/trigger-investigation", json={})
        assert response2.status_code == 422

        data2 = response2.json()
        assert "detail" in data2
