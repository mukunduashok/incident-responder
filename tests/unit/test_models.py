"""Unit tests for API models."""

import pytest
from pydantic import ValidationError

from src.incident_responder.api.models import (
    ErrorResponse,
    HealthResponse,
    InvestigationRequest,
    InvestigationResponse,
)


class TestInvestigationRequest:
    """Test InvestigationRequest model."""

    def test_creates_with_required_fields(self):
        """Should create request with required fields."""
        request = InvestigationRequest(
            service_name="payment-service", alert_type="database_timeout"
        )
        assert request.service_name == "payment-service"
        assert request.alert_type == "database_timeout"
        assert request.timestamp is None

    def test_creates_with_all_fields(self):
        """Should create request with all fields."""
        request = InvestigationRequest(
            service_name="payment-service",
            alert_type="database_timeout",
            timestamp="2026-01-23T14:23:45.123",
        )
        assert request.service_name == "payment-service"
        assert request.alert_type == "database_timeout"
        assert request.timestamp == "2026-01-23T14:23:45.123"

    def test_requires_service_name(self):
        """Should require service_name field."""
        with pytest.raises(ValidationError):
            InvestigationRequest(alert_type="database_timeout")

    def test_requires_alert_type(self):
        """Should require alert_type field."""
        with pytest.raises(ValidationError):
            InvestigationRequest(service_name="payment-service")

    def test_timestamp_is_optional(self):
        """Timestamp field should be optional."""
        request = InvestigationRequest(service_name="test-service", alert_type="error")
        assert request.timestamp is None

    def test_accepts_various_service_names(self):
        """Should accept various service name formats."""
        service_names = [
            "payment-service",
            "user_service",
            "ApiGateway",
            "service-123",
        ]
        for name in service_names:
            request = InvestigationRequest(service_name=name, alert_type="error")
            assert request.service_name == name

    def test_accepts_various_alert_types(self):
        """Should accept various alert type formats."""
        alert_types = ["database_timeout", "high_cpu", "memory-leak", "500_errors"]
        for alert in alert_types:
            request = InvestigationRequest(service_name="test", alert_type=alert)
            assert request.alert_type == alert


class TestInvestigationResponse:
    """Test InvestigationResponse model."""

    def test_creates_with_all_fields(self):
        """Should create response with all required fields."""
        response = InvestigationResponse(
            investigation_id="test-123",
            status="pending",
            message="Investigation started",
            report_path="reports/postmortem_test-123.md",
            started_at="2026-01-23T14:23:45.123",
        )
        assert response.investigation_id == "test-123"
        assert response.status == "pending"
        assert response.message == "Investigation started"
        assert response.report_path == "reports/postmortem_test-123.md"
        assert response.started_at == "2026-01-23T14:23:45.123"

    def test_requires_investigation_id(self):
        """Should require investigation_id field."""
        with pytest.raises(ValidationError):
            InvestigationResponse(
                status="pending",
                message="Test",
                started_at="2026-01-23T14:23:45.123",
            )

    def test_requires_status(self):
        """Should require status field."""
        with pytest.raises(ValidationError):
            InvestigationResponse(
                investigation_id="test-123",
                message="Test",
                started_at="2026-01-23T14:23:45.123",
            )

    def test_requires_message(self):
        """Should require message field."""
        with pytest.raises(ValidationError):
            InvestigationResponse(
                investigation_id="test-123",
                status="pending",
                started_at="2026-01-23T14:23:45.123",
            )

    def test_requires_started_at(self):
        """Should require started_at field."""
        with pytest.raises(ValidationError):
            InvestigationResponse(
                investigation_id="test-123", status="pending", message="Test"
            )

    def test_report_path_is_optional(self):
        """Report path should be optional."""
        response = InvestigationResponse(
            investigation_id="test-123",
            status="pending",
            message="Test",
            started_at="2026-01-23T14:23:45.123",
        )
        assert response.report_path is None


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_creates_with_all_fields(self):
        """Should create health response with all fields."""
        response = HealthResponse(
            status="healthy",
            llm_configured=True,
            logs_available=True,
            git_repo_available=True,
            timestamp="2026-01-23T14:23:45.123",
        )
        assert response.status == "healthy"
        assert response.llm_configured is True
        assert response.logs_available is True
        assert response.git_repo_available is True
        assert response.timestamp == "2026-01-23T14:23:45.123"

    def test_requires_all_boolean_fields(self):
        """Should require all boolean health check fields."""
        with pytest.raises(ValidationError):
            HealthResponse(
                status="healthy", llm_configured=True, timestamp="2026-01-23"
            )

    def test_accepts_false_values(self):
        """Should accept False for boolean fields."""
        response = HealthResponse(
            status="unhealthy",
            llm_configured=False,
            logs_available=False,
            git_repo_available=False,
            timestamp="2026-01-23T14:23:45.123",
        )
        assert response.llm_configured is False
        assert response.logs_available is False
        assert response.git_repo_available is False


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_creates_with_error_message(self):
        """Should create error response with error message."""
        response = ErrorResponse(error="Test error message")
        assert response.error == "Test error message"
        assert response.detail is None

    def test_creates_with_error_and_detail(self):
        """Should create error response with error and detail."""
        response = ErrorResponse(
            error="Test error", detail="Detailed error information"
        )
        assert response.error == "Test error"
        assert response.detail == "Detailed error information"

    def test_requires_error_field(self):
        """Should require error field."""
        with pytest.raises(ValidationError):
            ErrorResponse(detail="Detail only")

    def test_detail_is_optional(self):
        """Detail field should be optional."""
        response = ErrorResponse(error="Error")
        assert response.detail is None


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_investigation_request_to_dict(self):
        """Should serialize InvestigationRequest to dict."""
        request = InvestigationRequest(
            service_name="test-service",
            alert_type="error",
            timestamp="2026-01-23T14:23:45.123",
        )
        data = request.model_dump()
        assert isinstance(data, dict)
        assert data["service_name"] == "test-service"
        assert data["alert_type"] == "error"
        assert data["timestamp"] == "2026-01-23T14:23:45.123"

    def test_investigation_response_to_json(self):
        """Should serialize InvestigationResponse to JSON."""
        response = InvestigationResponse(
            investigation_id="test-123",
            status="pending",
            message="Test",
            started_at="2026-01-23T14:23:45.123",
        )
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        assert "test-123" in json_str
        assert "pending" in json_str

    def test_health_response_to_dict(self):
        """Should serialize HealthResponse to dict."""
        response = HealthResponse(
            status="healthy",
            llm_configured=True,
            logs_available=True,
            git_repo_available=True,
            timestamp="2026-01-23T14:23:45.123",
        )
        data = response.model_dump()
        assert data["status"] == "healthy"
        assert data["llm_configured"] is True
