"""Application-wide constants and configuration values.

This module centralizes all magic numbers, magic strings, and repeated values
to improve maintainability and follow DRY principles.
"""

# ============================================================================
# API Configuration
# ============================================================================

# API Metadata
API_TITLE = "Incident Responder API"
API_VERSION = "0.1.0"
API_DESCRIPTION = """
Intelligent DevOps Incident Responder - Multi-Agent System

Automatically investigates production incidents by:
1. Analyzing logs for error patterns
2. Searching git commits for recent changes
3. Generating comprehensive post-mortem reports

Built with CrewAI multi-agent orchestration.
"""

# API Endpoints
API_PREFIX = "/api/v1"
API_TAGS = ["investigations"]
DOCS_URL = "/docs"
REDOC_URL = "/redoc"

# CORS Configuration
CORS_ALLOW_ORIGINS = ["*"]  # Configure appropriately for production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]

# Default API Settings
DEFAULT_API_HOST = "0.0.0.0"
DEFAULT_API_PORT = "8000"

# ============================================================================
# LLM Configuration
# ============================================================================

# Ollama Defaults
DEFAULT_OLLAMA_MODEL = "minimax-m2.5:cloud"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"

# Ollama Cloud (for main LLM agents)
DEFAULT_OLLAMA_CLOUD_BASE_URL = "https://api.ollama.ai/v1"

# Local Ollama (for embeddings)
DEFAULT_EMBEDDING_MODEL = "embeddinggemma:latest"
DEFAULT_EMBEDDING_BASE_URL = "http://localhost:11434"

# LLM Parameters
LLM_TEMPERATURE = 0.3  # Lower temperature for more deterministic outputs

# ============================================================================
# Path Defaults
# ============================================================================

DEFAULT_LOG_DIRECTORY = "data/logs"
DEFAULT_REPORTS_DIRECTORY = "reports"
DEFAULT_GIT_REPO_PATH = "data/mock_repo"

# ============================================================================
# Investigation Status
# ============================================================================

# Investigation status values
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_HEALTHY = "healthy"

# ============================================================================
# Git Search Configuration
# ============================================================================

# Git commit defaults
DEFAULT_MAX_COMMITS = 5
GIT_SHORT_HASH_LENGTH = 8
MAX_FILES_TO_DISPLAY = 5

# Git log format string
GIT_LOG_FORMAT = "%H|%an|%ai|%s"

# Risk levels
RISK_LEVEL_HIGH = "HIGH"
RISK_LEVEL_MEDIUM = "MEDIUM"
RISK_LEVEL_LOW = "LOW"

# Risk assessment patterns
HIGH_RISK_PATTERNS = [
    "migration",
    "database",
    "schema",
    ".sql",
    "config.yaml",
    "config.json",
    "settings",
    "requirements.txt",
    "package.json",
    "dependencies",
]

MEDIUM_RISK_PATTERNS = [
    "api",
    "endpoint",
    "route",
    "handler",
    "service.py",
    "controller",
    "middleware",
]

HIGH_RISK_KEYWORDS = ["critical", "hotfix", "urgent", "breaking"]

# ============================================================================
# Log Parsing Configuration
# ============================================================================

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARN = "WARN"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"
LOG_LEVEL_FATAL = "FATAL"

# Error levels that should be extracted
ERROR_LEVELS = [LOG_LEVEL_ERROR, LOG_LEVEL_CRITICAL, LOG_LEVEL_FATAL]

# Error categories
ERROR_CATEGORY_DATABASE = "Database"
ERROR_CATEGORY_HTTP = "HTTP/Network"
ERROR_CATEGORY_NULL_POINTER = "NullPointer/Attribute"
ERROR_CATEGORY_STACK_TRACE = "Exception/StackTrace"
ERROR_CATEGORY_GENERAL = "General"

# Sample sizes
MAX_SAMPLE_ERRORS = 10
MAX_ERROR_MESSAGE_LENGTH = 200

# ============================================================================
# Report Generation Configuration
# ============================================================================

# Report filename format
REPORT_FILENAME_PREFIX = "postmortem"
REPORT_FILENAME_EXTENSION = ".md"

# ============================================================================
# HTTP Status Codes
# ============================================================================

HTTP_STATUS_OK = 200
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_INTERNAL_ERROR = 500

# ============================================================================
# Environment Variables
# ============================================================================

# Environment variable names
ENV_OLLAMA_MODEL = "OLLAMA_MODEL"
ENV_OLLAMA_BASE_URL = "OLLAMA_BASE_URL"
ENV_OLLAMA_API_KEY = "OLLAMA_API_KEY"
ENV_EMBEDDING_MODEL = "EMBEDDING_MODEL"
ENV_EMBEDDING_BASE_URL = "EMBEDDING_BASE_URL"
ENV_LOG_DIRECTORY = "LOG_DIRECTORY"
ENV_REPORTS_DIRECTORY = "REPORTS_DIRECTORY"
ENV_GIT_REPO_PATH = "GIT_REPO_PATH"
ENV_API_HOST = "API_HOST"
ENV_API_PORT = "API_PORT"

# ============================================================================
# GitHub Configuration
# ============================================================================

DEFAULT_GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION = "application/vnd.github.v3+json"
GITHUB_USER_AGENT = "incident-responder"

# GitHub Actions URL patterns
GITHUB_ACTIONS_RUN_URL_PATTERN = r"/actions/runs/(\d+)"

# Log source types
LOG_SOURCE_LOCAL = "local"
LOG_SOURCE_GITHUB_ACTIONS = "github-actions"
LOG_SOURCE_DATADOG = "datadog"

# Git source types
GIT_SOURCE_LOCAL = "local"
GIT_SOURCE_GITHUB = "github"
GIT_SOURCE_GITLAB = "gitlab"

# ============================================================================
# Timezone Configuration
# ============================================================================

DEFAULT_TIMEZONE = "UTC"

# ============================================================================
# File Patterns
# ============================================================================

LOG_FILE_EXTENSION = ".log"
GIT_DIRECTORY_NAME = ".git"
