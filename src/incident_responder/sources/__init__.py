"""Data source adapters for incident responder.

This package provides adapters for various data sources:
- GitHub Actions workflow logs
- Local log files
- Local git repositories

Usage:
    from incident_responder.sources import SourceFactory

    # Create a GitHub Actions source
    gh_source = SourceFactory.create_github_actions_source(token="...")

    # Or a local log source
    log_source = SourceFactory.create_log_source("local")
"""

from .base import (
    Commit,
    GitHubActionsSource,
    GitSource,
    LogEntry,
    LogSource,
    WorkflowRun,
)
from .factory import SourceFactory
from .github_actions import GitHubActionsAdapter
from .local import LocalLogAdapter
from .local_git import LocalGitAdapter

__all__ = [
    # Base interfaces
    "Commit",
    "LogEntry",
    "WorkflowRun",
    "GitSource",
    "LogSource",
    "GitHubActionsSource",
    # Adapters
    "GitHubActionsAdapter",
    "LocalLogAdapter",
    "LocalGitAdapter",
    # Factory
    "SourceFactory",
]
