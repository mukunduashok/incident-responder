"""Base interfaces for data source adapters."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Commit:
    """Represents a git commit."""

    hash: str
    author: str
    date: datetime
    message: str
    diff: str | None = None
    files_changed: list[str] | None = None


@dataclass
class LogEntry:
    """Represents a log entry."""

    timestamp: datetime
    level: str
    message: str
    metadata: dict
    source: str | None = None  # e.g., "github-actions", "datadog"


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""

    id: int
    name: str
    status: str  # "queued", "in_progress", "completed"
    conclusion: str | None  # "success", "failure", "cancelled", None if not completed
    workflow_id: int
    head_branch: str
    head_sha: str
    run_number: int
    event: str  # "push", "pull_request", etc.
    created_at: datetime
    updated_at: datetime
    html_url: str
    logs_url: str | None = None
    jobs_url: str | None = None


class GitSource(ABC):
    """Abstract base class for git data sources."""

    @abstractmethod
    def get_commits(
        self,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        branch: str | None = None,
    ) -> Iterator[Commit]:
        """
        Get commits from the repository.

        Args:
            repo: Repository in format "owner/repo"
            since: Start date for commits
            until: End date for commits
            branch: Branch to filter commits

        Yields:
            Commit objects
        """
        pass


class LogSource(ABC):
    """Abstract base class for log data sources."""

    @abstractmethod
    def get_logs(
        self,
        service: str,
        since: datetime,
        until: datetime,
        level: str | None = None,
    ) -> Iterator[LogEntry]:
        """
        Get log entries for a service.

        Args:
            service: Service name or identifier
            since: Start time for logs
            until: End time for logs
            level: Filter by log level (e.g., "ERROR", "WARNING")

        Yields:
            LogEntry objects
        """
        pass


class GitHubActionsSource(ABC):
    """Abstract base class for GitHub Actions log sources."""

    @abstractmethod
    def get_workflow_run(
        self,
        repo: str,
        run_id: int | None = None,
        run_url: str | None = None,
    ) -> WorkflowRun:
        """
        Get a specific workflow run.

        Args:
            repo: Repository in format "owner/repo"
            run_id: Workflow run ID
            run_url: Workflow run URL

        Returns:
            WorkflowRun object

        Raises:
            ValueError: If neither run_id nor run_url is provided
        """
        pass

    @abstractmethod
    def get_workflow_runs(
        self,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        status: str | None = None,  # "queued", "in_progress", "completed"
    ) -> Iterator[WorkflowRun]:
        """
        Get workflow runs for a repository.

        Args:
            repo: Repository in format "owner/repo"
            since: Start time for runs
            until: End time for runs
            status: Filter by run status

        Yields:
            WorkflowRun objects
        """
        pass

    @abstractmethod
    def get_workflow_logs(
        self,
        repo: str,
        run_id: int | None = None,
        run_url: str | None = None,
    ) -> Iterator[LogEntry]:
        """
        Get logs for a specific workflow run.

        Args:
            repo: Repository in format "owner/repo"
            run_id: Workflow run ID
            run_url: Workflow run URL

        Yields:
            LogEntry objects for each job/step in the workflow
        """
        pass
