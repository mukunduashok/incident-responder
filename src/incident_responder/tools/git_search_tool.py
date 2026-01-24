"""Custom tool for searching git commits."""

import subprocess
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class GitSearchInput(BaseModel):
    """Input schema for GitSearchTool."""

    git_repo_path: str = Field(..., description="Path to the git repository")
    timestamp: str = Field(
        ..., description="Timestamp to search commits before (ISO format)"
    )
    max_commits: int = Field(
        default=5, description="Maximum number of commits to retrieve"
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

    def _run(self, git_repo_path: str, timestamp: str, max_commits: int = 5) -> str:
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

            if not (repo_path / ".git").exists():
                return f"Error: Not a valid git repository at {repo_path}"

            # Get recent commits using git log
            # Format: hash|author|date|subject
            # Force UTC timezone to match ISO timestamps
            import os

            env = os.environ.copy()
            env["TZ"] = "UTC"

            cmd = [
                "git",
                "-C",
                str(repo_path),
                "log",
                f"-{max_commits}",
                "--pretty=format:%H|%an|%ai|%s",
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
                    files_cmd = [
                        "git",
                        "-C",
                        str(repo_path),
                        "show",
                        "--name-only",
                        "--pretty=format:",
                        hash_val,
                    ]
                    files_result = subprocess.run(
                        files_cmd, capture_output=True, text=True
                    )
                    changed_files = [
                        f for f in files_result.stdout.strip().split("\n") if f
                    ]

                    # Assess risk based on changed files
                    risk = self._assess_risk(changed_files, subject)

                    commits.append(
                        {
                            "hash": hash_val[:8],  # Short hash
                            "author": author,
                            "date": date,
                            "message": subject,
                            "files_changed": changed_files,
                            "risk_level": risk,
                        }
                    )

            # Format output
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
                for file in commit["files_changed"][:5]:  # Show first 5 files
                    output.append(f"     - {file}")
                if len(commit["files_changed"]) > 5:
                    output.append(
                        f"     ... and {len(commit['files_changed']) - 5} more"
                    )

            return "\n".join(output)

        except subprocess.CalledProcessError as e:
            return f"Error executing git command: {e.stderr}"
        except Exception as e:
            return f"Error searching git commits: {str(e)}"

    def _assess_risk(self, files: list, message: str) -> str:
        """
        Assess risk level based on changed files and commit message.

        Args:
            files: List of changed file paths
            message: Commit message

        Returns:
            Risk level: HIGH, MEDIUM, or LOW
        """
        high_risk_patterns = [
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

        medium_risk_patterns = [
            "api",
            "endpoint",
            "route",
            "handler",
            "service.py",
            "controller",
            "middleware",
        ]

        # Check files
        for file in files:
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in high_risk_patterns):
                return "HIGH"

        for file in files:
            file_lower = file.lower()
            if any(pattern in file_lower for pattern in medium_risk_patterns):
                return "MEDIUM"

        # Check commit message
        message_lower = message.lower()
        if any(
            word in message_lower
            for word in ["critical", "hotfix", "urgent", "breaking"]
        ):
            return "HIGH"

        return "LOW"
