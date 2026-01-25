"""Custom tool for searching git commits."""

import os
import subprocess
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..constants import (
    DEFAULT_MAX_COMMITS,
    DEFAULT_TIMEZONE,
    GIT_DIRECTORY_NAME,
    GIT_LOG_FORMAT,
    GIT_SHORT_HASH_LENGTH,
    HIGH_RISK_KEYWORDS,
    HIGH_RISK_PATTERNS,
    MAX_FILES_TO_DISPLAY,
    MEDIUM_RISK_PATTERNS,
    RISK_LEVEL_HIGH,
    RISK_LEVEL_LOW,
    RISK_LEVEL_MEDIUM,
)


class GitSearchInput(BaseModel):
    """Input schema for GitSearchTool."""

    git_repo_path: str = Field(..., description="Path to the git repository")
    timestamp: str = Field(
        ..., description="Timestamp to search commits before (ISO format)"
    )
    max_commits: int = Field(
        default=DEFAULT_MAX_COMMITS,
        description="Maximum number of commits to retrieve",
    )


class GitSearchTool(BaseTool):
    """
    Custom tool for searching recent git commits.

    This tool searches a git repository for recent commits before a specified timestamp,
    extracting commit metadata, changed files, and assessing risk indicators.
    """

    name: str = "git_search"
    description: str = (
        "Searches a git repository for recent commits before a specified timestamp. "
        "Returns commit hash, message, author, timestamp, changed files, and risk assessment. "
        "Useful for correlating code changes with incidents. "
        "Input should include git_repo_path, timestamp, and optionally max_commits."
    )
    args_schema: type[BaseModel] = GitSearchInput

    def _run(
        self, git_repo_path: str, timestamp: str, max_commits: int = DEFAULT_MAX_COMMITS
    ) -> str:
        """
        Search git commits in the repository.

        Args:
            git_repo_path: Path to the git repository
            timestamp: Search commits before this timestamp
            max_commits: Maximum number of commits to retrieve

        Returns:
            Structured information about recent commits
        """
        try:
            repo_path = Path(git_repo_path)

            if not repo_path.exists():
                return f"Error: Repository not found at {repo_path}"

            if not (repo_path / GIT_DIRECTORY_NAME).exists():
                return f"Error: Not a valid git repository at {repo_path}"

            # Get recent commits using git log
            # Format: hash|author|date|subject
            # Force UTC timezone to match ISO timestamps
            env = os.environ.copy()
            env["TZ"] = DEFAULT_TIMEZONE

            cmd = [
                "git",
                "-C",
                str(repo_path),
                "log",
                f"-{max_commits}",
                f"--pretty=format:{GIT_LOG_FORMAT}",
                f"--before={timestamp}",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, env=env
            )

            if not result.stdout:
                return f"No commits found before {timestamp}"

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    hash_val, author, date, subject = line.split("|", 3)

                    # Get files changed in this commit
                    changed_files = self._get_changed_files(repo_path, hash_val)

                    # Assess risk based on changed files
                    risk = self._assess_risk(changed_files, subject)

                    commits.append(
                        {
                            "hash": hash_val[:GIT_SHORT_HASH_LENGTH],
                            "author": author,
                            "date": date,
                            "message": subject,
                            "files_changed": changed_files,
                            "risk_level": risk,
                        }
                    )

            # Format output
            output = self._format_commit_output(git_repo_path, timestamp, commits)

            return output

        except subprocess.CalledProcessError as e:
            return f"Error executing git command: {e.stderr}"
        except Exception as e:
            return f"Error searching git commits: {str(e)}"

    def _get_changed_files(self, repo_path: Path, commit_hash: str) -> list[str]:
        """
        Get list of files changed in a commit.

        Args:
            repo_path: Path to the git repository
            commit_hash: Commit hash to query

        Returns:
            List of changed file paths
        """
        files_cmd = [
            "git",
            "-C",
            str(repo_path),
            "show",
            "--name-only",
            "--pretty=format:",
            commit_hash,
        ]
        files_result = subprocess.run(files_cmd, capture_output=True, text=True)
        return [f for f in files_result.stdout.strip().split("\n") if f]

    def _format_commit_output(
        self, git_repo_path: str, timestamp: str, commits: list[dict]
    ) -> str:
        """
        Format commit information for output.

        Args:
            git_repo_path: Path to the git repository
            timestamp: Timestamp filter used
            commits: List of commit dictionaries

        Returns:
            Formatted string output
        """
        output = [
            "=== Git Commit Analysis ===\n",
            f"Repository: {git_repo_path}",
            f"Commits before: {timestamp}",
            f"Total commits found: {len(commits)}\n",
        ]

        for idx, commit in enumerate(commits, 1):
            output.append(f"\n{idx}. Commit {commit['hash']}")
            output.append(f"   Author: {commit['author']}")
            output.append(f"   Date: {commit['date']}")
            output.append(f"   Message: {commit['message']}")
            output.append(f"   Risk Level: {commit['risk_level']}")
            output.append(f"   Files Changed ({len(commit['files_changed'])}):")

            # Display first N files
            for file in commit["files_changed"][:MAX_FILES_TO_DISPLAY]:
                output.append(f"     - {file}")

            # Show overflow count
            if len(commit["files_changed"]) > MAX_FILES_TO_DISPLAY:
                remaining = len(commit["files_changed"]) - MAX_FILES_TO_DISPLAY
                output.append(f"     ... and {remaining} more")

        return "\n".join(output)

    def _assess_risk(self, files: list, message: str) -> str:
        """
        Assess risk level based on changed files and commit message.

        Args:
            files: List of changed file paths
            message: Commit message

        Returns:
            Risk level: HIGH, MEDIUM, or LOW
        """
        # Check files for high-risk patterns
        for file in files:
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in HIGH_RISK_PATTERNS):
                return RISK_LEVEL_HIGH

        # Check files for medium-risk patterns
        for file in files:
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in MEDIUM_RISK_PATTERNS):
                return RISK_LEVEL_MEDIUM

        # Check commit message for high-risk keywords
        message_lower = message.lower()
        if any(word in message_lower for word in HIGH_RISK_KEYWORDS):
            return RISK_LEVEL_HIGH

        return RISK_LEVEL_LOW
