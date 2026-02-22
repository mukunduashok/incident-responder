"""Factory for creating data source adapters."""

from ..constants import (
    DEFAULT_GITHUB_API_URL,
    GIT_SOURCE_LOCAL,
    LOG_SOURCE_GITHUB_ACTIONS,
    LOG_SOURCE_LOCAL,
)
from .base import GitHubActionsSource, GitSource, LogSource
from .github_actions import GitHubActionsAdapter
from .local import LocalLogAdapter


class SourceFactory:
    """Factory for creating data source adapters."""

    @staticmethod
    def create_log_source(
        source_type: str,
        **kwargs,
    ) -> LogSource:
        """
        Create a log source adapter.

        Args:
            source_type: Type of log source
            **kwargs: Additional arguments for the adapter

        Returns:
            LogSource adapter instance
        """
        source_type = source_type.lower()

        if source_type == LOG_SOURCE_LOCAL:
            return LocalLogAdapter(
                log_directory=kwargs.get("log_directory"),
            )
        elif source_type == LOG_SOURCE_GITHUB_ACTIONS:
            raise ValueError(
                "GitHub Actions requires GitHubActionsSource. Use create_github_actions_source()"
            )
        else:
            raise ValueError(f"Unknown log source type: {source_type}")

    @staticmethod
    def create_github_actions_source(
        token: str | None = None,
        api_url: str = DEFAULT_GITHUB_API_URL,
    ) -> GitHubActionsSource:
        """
        Create a GitHub Actions source adapter.

        Args:
            token: GitHub personal access token
            api_url: GitHub API URL

        Returns:
            GitHubActionsSource adapter instance
        """
        return GitHubActionsAdapter(
            token=token,
            api_url=api_url,
        )

    @staticmethod
    def create_git_source(
        source_type: str,
        **kwargs,
    ) -> GitSource:
        """
        Create a git source adapter.

        Args:
            source_type: Type of git source
            **kwargs: Additional arguments for the adapter

        Returns:
            GitSource adapter instance
        """
        source_type = source_type.lower()

        if source_type == GIT_SOURCE_LOCAL:
            from .local_git import LocalGitAdapter

            return LocalGitAdapter(
                repo_path=kwargs.get("repo_path"),
            )
        else:
            raise ValueError(f"Unknown git source type: {source_type}")
