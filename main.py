"""Main entry point for the Incident Responder API."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.incident_responder.api.routes import router
from src.incident_responder.utils.config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Incident Responder API",
    description="""
    Intelligent DevOps Incident Responder - Multi-Agent System

    Automatically investigates production incidents by:
    1. Analyzing logs for error patterns
    2. Searching git commits for recent changes
    3. Generating comprehensive post-mortem reports

    Built with CrewAI multi-agent orchestration.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1", tags=["investigations"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Incident Responder API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "trigger_investigation": "/api/v1/trigger-investigation",
            "get_investigation": "/api/v1/investigation/{id}",
        },
    }


def main():
    """Run the FastAPI application."""
    print("🚀 Starting Incident Responder API...")
    print(f"📁 Log Directory: {Config.LOG_DIRECTORY}")
    print(f"📄 Reports Directory: {Config.REPORTS_DIRECTORY}")
    print(f"🔧 Git Repo Path: {Config.GIT_REPO_PATH}")
    print(f"🤖 LLM Model: {Config.AZURE_DEPLOYMENT_NAME}")
    print(f"\n📚 API Documentation: http://{Config.API_HOST}:{Config.API_PORT}/docs")

    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT, log_level="info")


if __name__ == "__main__":
    main()
