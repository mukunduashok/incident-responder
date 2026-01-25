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
    STATUS_PENDING,
)

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.mark.parametrize(
    "endpoint,method,payload,required_fields,extra_checks",
    [
        (
            "/health",
            "get",
            None,
            [
                "status",
                "llm_configured",
                "logs_available",
                "git_repo_available",
                "timestamp",
            ],
            lambda data: (
                isinstance(data["status"], str)
                and isinstance(data["llm_configured"], bool)
                and isinstance(data["logs_available"], bool)
                and isinstance(data["git_repo_available"], bool)
                and isinstance(data["timestamp"], str)
                and ("T" in data["timestamp"] or " " in data["timestamp"])
                and ":" in data["timestamp"]
            ),
        ),
        (
            "/trigger-investigation",
            "post",
            {"service_name": "test", "alert_type": "error"},
            ["investigation_id", "status", "message", "started_at"],
            lambda data: True,
        ),
    ],
)
def test_api_response_formats(endpoint, method, payload, required_fields, extra_checks):
    """Parametrized test for endpoint response formats and field types."""
    if method == "get":
        response = client.get(endpoint)
    else:
        response = client.post(endpoint, json=payload)
    data = response.json()
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    assert extra_checks(data)


# Positive integration tests for investigation workflow


@pytest.mark.parametrize(
    "payload,expected_service,expected_alert,check_timestamp",
    [
        (  # Default timestamp
            {"service_name": "user-service", "alert_type": "high_latency"},
            "user-service",
            "high_latency",
            True,
        ),
        (  # Explicit timestamp
            {
                "service_name": "payment-processor",
                "alert_type": "timeout_error",
                "timestamp": "2026-01-25T10:30:00.000",
            },
            "payment-processor",
            "timeout_error",
            True,
        ),
    ],
)
def test_investigation_preserves_input_and_timestamp(
    payload, expected_service, expected_alert, check_timestamp
):
    """Investigation should preserve input data and track timestamp/start time."""
    trigger_response = client.post("/trigger-investigation", json=payload)
    assert trigger_response.status_code == 200
    data = trigger_response.json()
    investigation_id = data["investigation_id"]
    assert investigation_id is not None
    assert data["status"] == STATUS_PENDING
    assert "started_at" in data
    started_at = data["started_at"]
    assert isinstance(started_at, str)
    assert len(started_at) > 0

    # Get status to verify input preservation
    status_response = client.get(f"/investigation/{investigation_id}")
    status_data = status_response.json()
    assert status_data["service_name"] == expected_service
    assert status_data["alert_type"] == expected_alert
    if check_timestamp:
        assert "timestamp" in status_data
        assert status_data["timestamp"] is not None


def test_investigation_id_is_valid_uuid():
    """Investigation ID should be a valid UUID."""
    payload = {"service_name": "test-service", "alert_type": "error"}
    response = client.post("/trigger-investigation", json=payload)
    investigation_id = response.json()["investigation_id"]
    try:
        uuid.UUID(investigation_id)
    except ValueError:
        pytest.fail(f"Investigation ID {investigation_id} is not a valid UUID")


# Negative integration tests for investigation workflow


@pytest.mark.parametrize(
    "payload,expected_status,invalid_json,nonexistent_id",
    [
        ({"alert_type": "error"}, 422, False, False),  # Missing service_name
        ({"service_name": "test"}, 422, False, False),  # Missing alert_type
        ({}, 422, False, False),  # Empty payload
        (None, 422, True, False),  # Invalid JSON
        (None, 404, False, True),  # Nonexistent investigation
    ],
)
def test_investigation_negative_cases(
    payload, expected_status, invalid_json, nonexistent_id
):
    """Parametrized negative/validation error scenarios."""
    if invalid_json:
        with TestClient(app) as test_client:
            resp = test_client.post(
                "/trigger-investigation",
                content=b"not json",
                headers={"Content-Type": "application/json"},
            )
            assert resp.status_code == expected_status
        return
    if nonexistent_id:
        fake_id = str(uuid.uuid4())
        response = client.get(f"/investigation/{fake_id}")
        assert response.status_code == expected_status
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        return
    response = client.post("/trigger-investigation", json=payload)
    assert response.status_code == expected_status
