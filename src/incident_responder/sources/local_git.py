"""Local git repository adapter."""

import os
import subprocess
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from ..constants import (
    DEFAULT_GIT_REPO_PATH,
    DEFAULT_TIMEZONE,
    GIT_DIRECTORY_NAME,
)
from . import Commit, GitSource


class LocalGitAdapter(GitSource):
    """Adapter for reading git commits from a local repository."""

    # Git log format: hash|author|date|message|refs
    _LOG_FORMAT = "%H|%an|%ai|%s|%D"

    def __init__(
        self,
        repo_path: str | None = None,
    ):
        """
        Initialize the local git adapter.

        Args:
            repo_path: Path to the git repository (default: from Config)
        """
        self.repo_path = Path(repo_path or DEFAULT_GIT_REPO_PATH)

    def _validate_repository(self) -> None:
        """Validate that the repository exists and is a valid git repo."""
        if not self.repo_path.exists():
            raise ValueError(f"Repository not found at {self.repo_path}")

        if not (self.repo_path / GIT_DIRECTORY_NAME).exists():
            raise ValueError(f"Not a valid git repository at {self.repo_path}")

    def _build_git_command(
        self,
        branch: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[str]:
        """Build git log command with filters."""
        cmd = [
            "git",
            "-C",
            str(self.repo_path),
            "log",
            f"--pretty=format:{self._LOG_FORMAT}",
        ]

        # Add branch filter
        if branch:
            cmd.append(branch)

        # Add date filters
        if until:
            cmd.append(f"--until={until.isoformat()}")
        if since:
            cmd.append(f"--since={since.isoformat()}")

        return cmd

    def _get_env_with_timezone(self) -> dict:
        """Get environment with UTC timezone for consistent git output."""
        env = os.environ.copy()
        env["TZ"] = DEFAULT_TIMEZONE
        return env

    def get_commits(
        self,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        branch: str | None = None,
    ) -> Iterator[Commit]:
        """
        Get commits from the local repository.

        Args:
            repo: Repository name (ignored for local, uses self.repo_path)
            since: Start date for commits
            until: End date for commits
            branch: Branch to filter commits

        Yields:
            Commit objects
        """
        self._validate_repository()

        cmd = self._build_git_command(branch=branch, since=since, until=until)
        env = self._get_env_with_timezone()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                commit = self._parse_commit_line(line)
                if commit:
                    yield commit

        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error executing git command: {e.stderr}") from e

    def _parse_commit_line(self, line: str) -> Commit | None:
        """Parse a git log line into a Commit object."""
        # Format: hash|author|date|message|refs
        parts = line.split("|", 4)
        if len(parts) < 4:
            return None

        hash_val, author, date_str, message = parts[0], parts[1], parts[2], parts[3]
        date = self._parse_date(date_str)
        diff = self._get_commit_diff(hash_val)

        return Commit(
            hash=hash_val,
            author=author,
            date=date,
            message=message,
            diff=diff,
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string from git log."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now()

    def _get_commit_diff(self, commit_hash: str) -> str | None:
        """Get the diff for a specific commit."""
        try:
            cmd = [
                "git",
                "-C",
                str(self.repo_path),
                "show",
                commit_hash,
                "--pretty=format:",
                "--patch",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout or None
        except subprocess.CalledProcessError:
            return None
