"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
    """Request model for triggering an investigation."""

    service_name: str = Field(
        ...,
        description="Name of the service to investigate (e.g., 'payment-service')",
        example="payment-service",
    )
    alert_type: str = Field(
        ...,
        description="Type of alert that triggered the investigation",
        example="database_timeout",
    )
    timestamp: str | None = Field(
        default=None,
        description="Timestamp when the incident occurred (ISO format). Defaults to now.",
        example="2026-01-23T14:23:45.123",
    )


class InvestigationResponse(BaseModel):
    """Response model for investigation trigger."""

    investigation_id: str = Field(..., description="Unique ID for this investigation")
    status: str = Field(..., description="Status of the investigation")
    message: str = Field(..., description="Human-readable message")
    report_path: str | None = Field(None, description="Path to the generated report")
    started_at: str = Field(..., description="When the investigation started")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Overall service status")
    llm_configured: bool = Field(..., description="Whether LLM is properly configured")
    logs_available: bool = Field(..., description="Whether log directory exists")
    git_repo_available: bool = Field(..., description="Whether git repository exists")
    timestamp: str = Field(..., description="Current server time")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")
