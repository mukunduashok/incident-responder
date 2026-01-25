"""Main entry point for the Incident Responder API."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.incident_responder.api.routes import router
from src.incident_responder.constants import (
    API_DESCRIPTION,
    API_PREFIX,
    API_TAGS,
    API_TITLE,
    API_VERSION,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_ORIGINS,
    DOCS_URL,
    REDOC_URL,
)
from src.incident_responder.utils.config import Config

# Initialize FastAPI app
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=API_VERSION,
    docs_url=DOCS_URL,
    redoc_url=REDOC_URL,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Include API routes
app.include_router(router, prefix=API_PREFIX, tags=API_TAGS)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "status": "running",
        "docs": DOCS_URL,
        "endpoints": {
            "health": f"{API_PREFIX}/health",
            "trigger_investigation": f"{API_PREFIX}/trigger-investigation",
            "get_investigation": f"{API_PREFIX}/investigation/{{id}}",
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
