"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.incident_responder.api.routes import router
from fastapi import FastAPI

# Create a test app
app = FastAPI()
app.include_router(router)

client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_response_structure(self):
        """Test that health check returns expected fields."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "llm_configured" in data
        assert "logs_available" in data
        assert "git_repo_available" in data
        assert "timestamp" in data


class TestInvestigationEndpoint:
    """Tests for investigation endpoints."""
    
    def test_trigger_investigation_accepts_valid_request(self):
        """Test that trigger investigation accepts valid requests."""
        payload = {
            "service_name": "payment-service",
            "alert_type": "database_timeout",
            "timestamp": "2026-01-23T14:23:45.123"
        }
        
        response = client.post("/trigger-investigation", json=payload)
        assert response.status_code == 200
    
    def test_trigger_investigation_returns_investigation_id(self):
        """Test that trigger investigation returns an investigation ID."""
        payload = {
            "service_name": "payment-service",
            "alert_type": "database_timeout"
        }
        
        response = client.post("/trigger-investigation", json=payload)
        data = response.json()
        
        assert "investigation_id" in data
        assert "status" in data
        assert "message" in data
        assert data["status"] == "pending"
    
    def test_trigger_investigation_validates_input(self):
        """Test that trigger investigation validates input."""
        # Missing required field
        payload = {
            "alert_type": "database_timeout"
        }
        
        response = client.post("/trigger-investigation", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_get_investigation_status(self):
        """Test retrieving investigation status."""
        # First create an investigation
        payload = {
            "service_name": "payment-service",
            "alert_type": "database_timeout"
        }
        
        create_response = client.post("/trigger-investigation", json=payload)
        investigation_id = create_response.json()["investigation_id"]
        
        # Then retrieve its status
        status_response = client.get(f"/investigation/{investigation_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert "status" in status_data
        assert status_data["service_name"] == "payment-service"
    
    def test_get_nonexistent_investigation_returns_404(self):
        """Test that retrieving a nonexistent investigation returns 404."""
        response = client.get("/investigation/nonexistent-id-12345")
        assert response.status_code == 404
