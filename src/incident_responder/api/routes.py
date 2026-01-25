"""FastAPI routes for the Incident Responder API."""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..constants import (
    GIT_DIRECTORY_NAME,
    HTTP_STATUS_NOT_FOUND,
    REPORT_FILENAME_EXTENSION,
    REPORT_FILENAME_PREFIX,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_HEALTHY,
    STATUS_PENDING,
    STATUS_RUNNING,
)
from ..crew import IncidentResponderCrew
from ..utils.config import Config
from .models import (
    HealthResponse,
    InvestigationRequest,
    InvestigationResponse,
)

router = APIRouter()


# In-memory storage for investigation status (use database in production)
investigations = {}


def _update_investigation_status(
    investigation_id: str, status: str, **additional_fields
) -> None:
    """
    Update investigation status with additional fields.

    Args:
        investigation_id: Unique ID for this investigation
        status: New status value
        **additional_fields: Additional fields to update
    """
    investigations[investigation_id]["status"] = status
    investigations[investigation_id]["completed_at"] = datetime.now().isoformat()
    for key, value in additional_fields.items():
        investigations[investigation_id][key] = value


def run_investigation(investigation_id: str, inputs: dict):
    """
    Background task to run the CrewAI investigation.

    Args:
        investigation_id: Unique ID for this investigation
        inputs: Input parameters for the crew
    """
    try:
        investigations[investigation_id]["status"] = STATUS_RUNNING
        crew = IncidentResponderCrew().crew()
        result = crew.kickoff(inputs=inputs)

        # Update investigation status to completed
        _update_investigation_status(
            investigation_id, STATUS_COMPLETED, result=str(result)
        )

    except Exception as e:
        # Update investigation status to failed
        _update_investigation_status(investigation_id, STATUS_FAILED, error=str(e))


@router.post(
    "/trigger-investigation",
    response_model=InvestigationResponse,
    summary="Trigger incident investigation",
    description="Starts a multi-agent investigation of a production incident",
)
async def trigger_investigation(
    request: InvestigationRequest, background_tasks: BackgroundTasks
):
    """
    Trigger an incident investigation.

    This endpoint starts a multi-agent CrewAI workflow that:
    1. Analyzes logs for error patterns
    2. Searches git commits for recent changes
    3. Generates a comprehensive post-mortem report

    The investigation runs in the background, allowing you to query its status later.
    """
    # Generate unique investigation ID
    investigation_id = str(uuid.uuid4())

    # Use provided timestamp or current time
    timestamp = request.timestamp or datetime.now().isoformat()

    # Prepare inputs for the crew
    inputs = {
        "service_name": request.service_name,
        "timestamp": timestamp,
        "git_repo_path": str(Config.GIT_REPO_PATH),
        "investigation_id": investigation_id,
    }

    # Initialize investigation tracking
    investigations[investigation_id] = {
        "status": STATUS_PENDING,
        "service_name": request.service_name,
        "alert_type": request.alert_type,
        "timestamp": timestamp,
        "started_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }

    # Run investigation as a background task (fire and forget)
    background_tasks.add_task(run_investigation, investigation_id, inputs)

    # Generate report path
    report_path = f"reports/{REPORT_FILENAME_PREFIX}_{investigation_id}{REPORT_FILENAME_EXTENSION}"

    return InvestigationResponse(
        investigation_id=investigation_id,
        status=STATUS_PENDING,
        message=f"Investigation started for {request.service_name}",
        report_path=report_path,
        started_at=investigations[investigation_id]["started_at"],
    )


@router.get(
    "/investigation/{investigation_id}",
    summary="Get investigation status",
    description="Retrieve the status and results of an investigation",
)
async def get_investigation(investigation_id: str):
    """Get the status of an investigation by ID."""
    if investigation_id not in investigations:
        raise HTTPException(
            status_code=HTTP_STATUS_NOT_FOUND, detail="Investigation not found"
        )

    return investigations[investigation_id]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is healthy and properly configured",
)
async def health_check():
    """
    Health check endpoint.

    Verifies that:
    - LLM is configured
    - Log directory exists
    - Git repository is initialized
    """
    return HealthResponse(
        status=STATUS_HEALTHY,
        llm_configured=bool(Config.AZURE_DEPLOYMENT_NAME),
        logs_available=Config.LOG_DIRECTORY.exists(),
        git_repo_available=(Config.GIT_REPO_PATH / GIT_DIRECTORY_NAME).exists(),
        timestamp=datetime.now().isoformat(),
    )
