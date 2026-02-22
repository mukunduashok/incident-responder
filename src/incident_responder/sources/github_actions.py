"""GitHub Actions log source adapter."""

import re
from collections.abc import Iterator
from datetime import datetime

import requests

from ..constants import (
    DEFAULT_GITHUB_API_URL,
    GITHUB_ACTIONS_RUN_URL_PATTERN,
    GITHUB_API_VERSION,
    GITHUB_USER_AGENT,
)
from .base import GitHubActionsSource, LogEntry, WorkflowRun


class GitHubActionsAdapter(GitHubActionsSource):
    """Adapter for fetching GitHub Actions workflow runs and logs."""

    # Constants for log level mapping
    _CONCLUSION_TO_LEVEL = {
        "failure": "ERROR",
        "cancelled": "WARNING",
    }

    def __init__(
        self,
        token: str | None = None,
        api_url: str = DEFAULT_GITHUB_API_URL,
    ):
        """
        Initialize the GitHub Actions adapter.

        Args:
            token: GitHub personal access token for API authentication
            api_url: GitHub API base URL (default: https://api.github.com)
        """
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self.session.headers["Accept"] = GITHUB_API_VERSION
        self.session.headers["User-Agent"] = GITHUB_USER_AGENT

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make an authenticated request to the GitHub API."""
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    def _parse_repo(self, repo: str) -> tuple[str, str]:
        """Parse repository string into owner and repo."""
        if "/" not in repo:
            raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/repo'")
        owner, repo_name = repo.split("/", 1)
        return owner, repo_name

    def _extract_run_id_from_url(self, run_url: str) -> int:
        """Extract run ID from a GitHub Actions run URL."""
        match = re.search(GITHUB_ACTIONS_RUN_URL_PATTERN, run_url)
        if not match:
            raise ValueError(f"Invalid GitHub Actions run URL: {run_url}")
        return int(match.group(1))

    def _parse_datetime(self, dt_string: str) -> datetime:
        """Parse datetime string from GitHub API to timezone-aware datetime."""
        return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))

    def _get_log_level(self, conclusion: str | None) -> str:
        """Map workflow conclusion to log level."""
        return self._CONCLUSION_TO_LEVEL.get(conclusion, "INFO")

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
        """
        if run_id is None and run_url is None:
            raise ValueError("Either run_id or run_url must be provided")

        if run_url and run_id is None:
            run_id = self._extract_run_id_from_url(run_url)

        owner, repo_name = self._parse_repo(repo)
        url = f"{self.api_url}/repos/{owner}/{repo_name}/actions/runs/{run_id}"

        response = self._request("GET", url)
        return self._parse_workflow_run(response.json())

    def get_workflow_runs(
        self,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        status: str | None = None,
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
        owner, repo_name = self._parse_repo(repo)

        params = {}
        if status:
            params["status"] = status
        if since:
            params["created"] = f">={since.isoformat()}"

        url = f"{self.api_url}/repos/{owner}/{repo_name}/actions/runs"

        while url:
            response = self._request("GET", url, params=params)
            data = response.json()

            for run_data in data.get("workflow_runs", []):
                run = self._parse_workflow_run(run_data)

                # Filter by until if specified
                if until and run.created_at > until:
                    continue

                yield run

            # Handle pagination
            url = response.links.get("next", {}).get("url")
            params = None  # params already in URL for next page

    def get_workflow_logs(
        self,
        repo: str,
        run_id: int | None = None,
        run_url: str | None = None,
    ) -> Iterator[LogEntry]:
        """
        Get logs for a specific workflow run.

        This fetches the jobs and their steps.

        Args:
            repo: Repository in format "owner/repo"
            run_id: Workflow run ID
            run_url: Workflow run URL

        Yields:
            LogEntry objects for each job/step in the workflow
        """
        if run_id is None and run_url is None:
            raise ValueError("Either run_id or run_url must be provided")

        if run_url and run_id is None:
            run_id = self._extract_run_id_from_url(run_url)

        owner, repo_name = self._parse_repo(repo)

        # Get jobs for the run
        url = f"{self.api_url}/repos/{owner}/{repo_name}/actions/runs/{run_id}/jobs"
        response = self._request("GET", url)
        data = response.json()

        for job_data in data.get("jobs", []):
            yield from self._parse_job_logs(repo, run_id, job_data)

    def _parse_job_logs(
        self,
        repo: str,
        run_id: int,
        job_data: dict,
    ) -> Iterator[LogEntry]:
        """Parse job data into log entries."""
        job_name = job_data.get("name", "Unknown Job")
        job_status = job_data.get("status", "unknown")
        job_conclusion = job_data.get("conclusion")

        # Create log entry for job status
        job_message = f"Job: {job_name} - Status: {job_status}"
        if job_conclusion:
            job_message += f", Conclusion: {job_conclusion}"

        yield LogEntry(
            timestamp=self._parse_datetime(
                job_data.get("started_at", datetime.now().isoformat())
            ),
            level=self._get_log_level(job_conclusion),
            message=job_message,
            metadata={
                "job_id": job_data.get("id"),
                "job_name": job_name,
                "status": job_status,
                "conclusion": job_conclusion,
                "run_id": run_id,
                "repo": repo,
            },
            source="github-actions",
        )

        # Parse steps
        for step_data in job_data.get("steps", []):
            yield from self._parse_step_logs(repo, run_id, job_data, step_data)

    def _parse_step_logs(
        self,
        repo: str,
        run_id: int,
        job_data: dict,
        step_data: dict,
    ) -> Iterator[LogEntry]:
        """Parse step data into log entry."""
        step_name = step_data.get("name", "Unknown Step")
        step_status = step_data.get("status", "unknown")
        step_conclusion = step_data.get("conclusion")

        step_message = f"Step: {step_name} - Status: {step_status}"
        if step_conclusion:
            step_message += f", Conclusion: {step_conclusion}"

        step_logs_url = None
        if step_data.get("logs"):
            step_logs_url = step_data["logs"].get("url")

        yield LogEntry(
            timestamp=self._parse_datetime(
                step_data.get("started_at", datetime.now().isoformat())
            ),
            level=self._get_log_level(step_conclusion),
            message=step_message,
            metadata={
                "job_id": job_data.get("id"),
                "job_name": job_data.get("name"),
                "step_name": step_name,
                "step_number": step_data.get("number"),
                "status": step_status,
                "conclusion": step_conclusion,
                "logs_url": step_logs_url,
                "run_id": run_id,
                "repo": repo,
            },
            source="github-actions",
        )

    def _parse_workflow_run(self, data: dict) -> WorkflowRun:
        """Parse a workflow run API response into a WorkflowRun object."""
        return WorkflowRun(
            id=data["id"],
            name=data.get("name", "Unknown"),
            status=data.get("status", "unknown"),
            conclusion=data.get("conclusion"),
            workflow_id=data.get("workflow_id", 0),
            head_branch=data.get("head_branch", ""),
            head_sha=data.get("head_sha", ""),
            run_number=data.get("run_number", 0),
            event=data.get("event", "unknown"),
            created_at=self._parse_datetime(
                data.get("created_at", datetime.now().isoformat())
            ),
            updated_at=self._parse_datetime(
                data.get("updated_at", datetime.now().isoformat())
            ),
            html_url=data.get("html_url", ""),
            logs_url=data.get("logs_url"),
            jobs_url=data.get("jobs_url"),
        )
