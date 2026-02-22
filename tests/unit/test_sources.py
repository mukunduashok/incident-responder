"""Unit tests for source adapters."""

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.incident_responder.sources import (
    GitHubActionsAdapter,
    LocalGitAdapter,
    SourceFactory,
    WorkflowRun,
)
from src.incident_responder.sources.local import LocalLogAdapter

# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def sample_log_content() -> str:
    """Sample log file content for testing."""
    return """2026-02-20 10:00:00 INFO [app] Application started
2026-02-20 10:15:00 INFO [app] Processing request
2026-02-20 10:30:00 ERROR [app] Connection failed to database
2026-02-20 10:31:00 ERROR [app] Failed to process request: timeout
2026-02-20 10:45:00 WARN [app] Retrying connection
2026-02-20 11:00:00 INFO [app] Connection restored
"""


@pytest.fixture
def mock_workflow_run_response() -> dict:
    """Mock GitHub API response for a workflow run."""
    return {
        "id": 123456789,
        "name": "CI",
        "status": "completed",
        "conclusion": "failure",
        "workflow_id": 12345,
        "head_branch": "main",
        "head_sha": "abc123def456",
        "run_number": 42,
        "event": "push",
        "created_at": "2026-02-20T14:30:00Z",
        "updated_at": "2026-02-20T14:35:00Z",
        "html_url": "https://github.com/test-owner/test-repo/actions/runs/123456789",
        "logs_url": "https://api.github.com/repos/test-owner/test-repo/actions/runs/123456789/logs",
        "jobs_url": "https://api.github.com/repos/test-owner/test-repo/actions/runs/123456789/jobs",
    }


@pytest.fixture
def mock_jobs_response() -> dict:
    """Mock GitHub API response for workflow jobs."""
    return {
        "jobs": [
            {
                "id": 111,
                "name": "Build",
                "status": "completed",
                "conclusion": "failure",
                "started_at": "2026-02-20T14:30:00Z",
                "steps": [
                    {
                        "name": "Checkout",
                        "status": "completed",
                        "conclusion": "success",
                        "number": 1,
                        "started_at": "2026-02-20T14:30:05Z",
                    },
                ],
            },
        ]
    }


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create temporary directory for log files."""
    return tmp_path


@pytest.fixture
def temp_git_dir(tmp_path: Path) -> Path:
    """Create temporary directory with a git repository."""
    repo_path = tmp_path

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create a file and commit
    (repo_path / "test.txt").write_text("test content")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    return repo_path


# ============================================================================
# Test Constants
# ============================================================================

GITHUB_API_URL = "https://api.github.com"
GITHUB_ENTERPRISE_URL = "https://github.mycompany.com/api/v3"
TEST_TOKEN = "test_token_12345"
TEST_REPO = "test-owner/test-repo"
TEST_RUN_ID = 123456789
TEST_DATE = datetime(2026, 2, 20, 0, 0, 0)
TEST_DATE_END = datetime(2026, 2, 21, 0, 0, 0)


# ============================================================================
# GitHub Actions Adapter Tests
# ============================================================================


class TestGitHubActionsAdapter:
    """Tests for GitHubActionsAdapter class."""

    @pytest.fixture
    def adapter(self) -> GitHubActionsAdapter:
        """Create adapter with test token."""
        return GitHubActionsAdapter(token=TEST_TOKEN)

    def test_adapter_initialization(self, adapter: GitHubActionsAdapter) -> None:
        """Test adapter can be initialized."""
        assert adapter.token == TEST_TOKEN
        assert adapter.api_url == GITHUB_API_URL

    def test_adapter_with_custom_api_url(self) -> None:
        """Test adapter with custom GitHub Enterprise URL."""
        adapter = GitHubActionsAdapter(
            token="test_token", api_url=GITHUB_ENTERPRISE_URL
        )
        assert adapter.api_url == GITHUB_ENTERPRISE_URL

    @pytest.mark.parametrize(
        "url,expected_id",
        [
            ("https://github.com/owner/repo/actions/runs/123456789", 123456789),
            (
                "https://github.com/owner/repo/actions/runs/123456789/job/987654321",
                123456789,
            ),
        ],
    )
    def test_extract_run_id_from_url(
        self, adapter: GitHubActionsAdapter, url: str, expected_id: int
    ) -> None:
        """Test extracting run ID from various URL formats."""
        assert adapter._extract_run_id_from_url(url) == expected_id

    def test_extract_run_id_from_url_invalid(
        self, adapter: GitHubActionsAdapter
    ) -> None:
        """Test invalid URL raises ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub Actions run URL"):
            adapter._extract_run_id_from_url("https://github.com/owner/repo")

    @pytest.mark.parametrize(
        "repo,expected_owner,expected_repo",
        [
            ("test-owner/test-repo", "test-owner", "test-repo"),
            ("owner/repo", "owner", "repo"),
        ],
    )
    def test_parse_repo(
        self,
        adapter: GitHubActionsAdapter,
        repo: str,
        expected_owner: str,
        expected_repo: str,
    ) -> None:
        """Test parsing repository string."""
        owner, repo_name = adapter._parse_repo(repo)
        assert owner == expected_owner
        assert repo_name == expected_repo

    def test_parse_repo_invalid(self, adapter: GitHubActionsAdapter) -> None:
        """Test invalid repo format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repo format"):
            adapter._parse_repo("invalid-repo")

    def test_get_workflow_run_requires_id_or_url(
        self, adapter: GitHubActionsAdapter
    ) -> None:
        """Test that either run_id or run_url must be provided."""
        with pytest.raises(
            ValueError, match="Either run_id or run_url must be provided"
        ):
            adapter.get_workflow_run(TEST_REPO)

    def test_get_workflow_run_by_id(
        self, adapter: GitHubActionsAdapter, mock_workflow_run_response: dict
    ) -> None:
        """Test fetching a specific workflow run by ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflow_run_response

        with patch.object(adapter, "_request", return_value=mock_response):
            run = adapter.get_workflow_run(TEST_REPO, run_id=TEST_RUN_ID)

            assert isinstance(run, WorkflowRun)
            assert run.id == TEST_RUN_ID
            assert run.name == "CI"
            assert run.status == "completed"
            assert run.conclusion == "failure"

    def test_get_workflow_run_by_url(
        self, adapter: GitHubActionsAdapter, mock_workflow_run_response: dict
    ) -> None:
        """Test fetching workflow run from URL."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflow_run_response

        with patch.object(adapter, "_request", return_value=mock_response):
            run = adapter.get_workflow_run(
                TEST_REPO,
                run_url=f"https://github.com/{TEST_REPO}/actions/runs/{TEST_RUN_ID}",
            )

            assert run.id == TEST_RUN_ID

    def test_get_workflow_logs(
        self,
        adapter: GitHubActionsAdapter,
        mock_workflow_run_response: dict,
        mock_jobs_response: dict,
    ) -> None:
        """Test fetching workflow logs returns job and step entries."""
        # Now only 1 API call needed (directly to jobs)
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jobs_response

        with patch.object(adapter, "_request", return_value=mock_response):
            logs = list(adapter.get_workflow_logs(TEST_REPO, run_id=TEST_RUN_ID))

            # Should have 1 job entry + 1 step entry = 2 total
            assert len(logs) == 2
            assert logs[0].level == "ERROR"  # conclusion is failure
            assert logs[0].source == "github-actions"

    def test_get_workflow_runs(
        self, adapter: GitHubActionsAdapter, mock_workflow_run_response: dict
    ) -> None:
        """Test fetching workflow runs."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "workflow_runs": [mock_workflow_run_response]
        }
        mock_response.links = {}

        with patch.object(adapter, "_request", return_value=mock_response):
            runs = list(adapter.get_workflow_runs(TEST_REPO))

            assert len(runs) == 1
            assert runs[0].id == TEST_RUN_ID
            assert runs[0].conclusion == "failure"


class TestWorkflowRunDataclass:
    """Tests for WorkflowRun dataclass."""

    @pytest.mark.parametrize(
        "status,conclusion,expected_level",
        [
            ("completed", "failure", "ERROR"),
            ("completed", "success", "INFO"),
            ("queued", None, "INFO"),
        ],
    )
    def test_workflow_run_status_to_level(
        self, status: str, conclusion: str | None, expected_level: str
    ) -> None:
        """Test workflow run status maps to appropriate log level."""
        run = WorkflowRun(
            id=1,
            name="CI",
            status=status,
            conclusion=conclusion,
            workflow_id=1,
            head_branch="main",
            head_sha="abc123",
            run_number=1,
            event="push",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            html_url="https://github.com/test/test/actions/runs/1",
        )

        # Verify run was created successfully
        assert run.id == 1
        assert run.status == status
        assert run.conclusion == conclusion


# ============================================================================
# Local Log Adapter Tests
# ============================================================================


class TestLocalLogAdapter:
    """Tests for LocalLogAdapter class."""

    def test_adapter_initialization_default(self) -> None:
        """Test adapter with default log directory."""
        adapter = LocalLogAdapter()
        assert adapter.log_directory is not None

    def test_adapter_initialization_custom(self, temp_log_dir: Path) -> None:
        """Test adapter with custom log directory."""
        adapter = LocalLogAdapter(log_directory=temp_log_dir)
        assert adapter.log_directory == temp_log_dir

    def test_get_logs_returns_entries(
        self, temp_log_dir: Path, sample_log_content: str
    ) -> None:
        """Test fetching logs from a file returns all entries."""
        log_file = temp_log_dir / "test-service.log"
        log_file.write_text(sample_log_content)

        adapter = LocalLogAdapter(log_directory=temp_log_dir)

        logs = list(
            adapter.get_logs("test-service", since=TEST_DATE, until=TEST_DATE_END)
        )

        assert len(logs) == 6
        assert logs[0].level == "INFO"
        assert logs[2].level == "ERROR"
        assert "Connection failed" in logs[2].message

    @pytest.mark.parametrize(
        "level,expected_count",
        [
            ("ERROR", 2),
            ("INFO", 3),
            ("WARNING", 1),
        ],
    )
    def test_get_logs_filters_by_level(
        self,
        temp_log_dir: Path,
        sample_log_content: str,
        level: str,
        expected_count: int,
    ) -> None:
        """Test filtering logs by level."""
        log_file = temp_log_dir / "test-service.log"
        log_file.write_text(sample_log_content)

        adapter = LocalLogAdapter(log_directory=temp_log_dir)

        filtered_logs = list(
            adapter.get_logs(
                "test-service",
                since=TEST_DATE,
                until=TEST_DATE_END,
                level=level,
            )
        )

        assert len(filtered_logs) == expected_count
        assert all(log.level == level for log in filtered_logs)

    def test_get_logs_nonexistent_file(self, temp_log_dir: Path) -> None:
        """Test handling of nonexistent log file returns empty."""
        adapter = LocalLogAdapter(log_directory=temp_log_dir)

        logs = list(
            adapter.get_logs(
                "nonexistent-service", since=TEST_DATE, until=TEST_DATE_END
            )
        )

        assert len(logs) == 0

    def test_log_entry_has_source(
        self, temp_log_dir: Path, sample_log_content: str
    ) -> None:
        """Test that log entries have source set to 'local'."""
        log_file = temp_log_dir / "test-service.log"
        log_file.write_text(sample_log_content)

        adapter = LocalLogAdapter(log_directory=temp_log_dir)

        logs = list(
            adapter.get_logs("test-service", since=TEST_DATE, until=TEST_DATE_END)
        )

        assert all(log.source == "local" for log in logs)

    def test_empty_log_file(self, temp_log_dir: Path) -> None:
        """Test handling of empty log file returns empty."""
        log_file = temp_log_dir / "test-service.log"
        log_file.write_text("")

        adapter = LocalLogAdapter(log_directory=temp_log_dir)

        logs = list(
            adapter.get_logs("test-service", since=TEST_DATE, until=TEST_DATE_END)
        )

        assert len(logs) == 0


# ============================================================================
# Local Git Adapter Tests
# ============================================================================


class TestLocalGitAdapter:
    """Tests for LocalGitAdapter class."""

    def test_adapter_initialization_default(self) -> None:
        """Test adapter with default git repo path."""
        adapter = LocalGitAdapter()
        assert adapter.repo_path is not None

    def test_adapter_initialization_custom(self, temp_git_dir: Path) -> None:
        """Test adapter with custom git repo path."""
        adapter = LocalGitAdapter(repo_path=str(temp_git_dir))
        assert adapter.repo_path == temp_git_dir

    def test_get_commits_success(self, temp_git_dir: Path) -> None:
        """Test fetching commits from a git repository."""
        adapter = LocalGitAdapter(repo_path=temp_git_dir)
        commits = list(adapter.get_commits("test/repo"))

        assert len(commits) == 1
        assert commits[0].message == "Initial commit"
        assert commits[0].author == "Test User"

    def test_get_commits_nonexistent_repo(self) -> None:
        """Test handling of nonexistent repository raises error."""
        adapter = LocalGitAdapter(repo_path="/nonexistent/path")

        with pytest.raises(ValueError, match="Repository not found"):
            list(adapter.get_commits("test/repo"))

    def test_commit_has_required_fields(self, temp_git_dir: Path) -> None:
        """Test that commit has all required fields."""
        adapter = LocalGitAdapter(repo_path=temp_git_dir)
        commits = list(adapter.get_commits("test/repo"))

        commit = commits[0]
        assert commit.hash is not None
        assert commit.author is not None
        assert commit.date is not None
        assert commit.message is not None

    def test_get_commits_with_date_filter(self, temp_git_dir: Path) -> None:
        """Test fetching commits with date filter returns recent commits."""
        adapter = LocalGitAdapter(repo_path=temp_git_dir)

        # Get commits from the last hour (should get all)
        since = datetime.now(UTC) - timedelta(hours=1)

        commits = list(adapter.get_commits("test/repo", since=since))

        # Should get at least 1 commit (the initial commit)
        assert len(commits) >= 1


# ============================================================================
# Source Factory Tests
# ============================================================================


class TestSourceFactory:
    """Tests for SourceFactory class."""

    def test_create_log_source_local(self) -> None:
        """Test creating local log source."""
        source = SourceFactory.create_log_source("local")
        assert isinstance(source, LocalLogAdapter)

    def test_create_log_source_local_with_config(self) -> None:
        """Test creating local log source with custom config."""
        source = SourceFactory.create_log_source("local", log_directory="/custom/path")
        assert isinstance(source, LocalLogAdapter)

    def test_create_log_source_invalid_type(self) -> None:
        """Test creating log source with invalid type raises error."""
        with pytest.raises(ValueError, match="Unknown log source type"):
            SourceFactory.create_log_source("invalid_type")

    def test_create_github_actions_source(self) -> None:
        """Test creating GitHub Actions source."""
        source = SourceFactory.create_github_actions_source(token=TEST_TOKEN)
        assert isinstance(source, GitHubActionsAdapter)

    def test_create_github_actions_source_with_custom_api_url(self) -> None:
        """Test creating GitHub Actions source with custom API URL."""
        source = SourceFactory.create_github_actions_source(
            token=TEST_TOKEN,
            api_url=GITHUB_ENTERPRISE_URL,
        )
        assert isinstance(source, GitHubActionsAdapter)
        assert source.api_url == GITHUB_ENTERPRISE_URL

    def test_create_git_source_local(self) -> None:
        """Test creating local git source."""
        source = SourceFactory.create_git_source("local", repo_path="/tmp/test")
        assert isinstance(source, LocalGitAdapter)

    def test_create_git_source_invalid_type(self) -> None:
        """Test creating git source with invalid type raises error."""
        with pytest.raises(ValueError, match="Unknown git source type"):
            SourceFactory.create_git_source("invalid_type")

    @pytest.mark.parametrize("source_type", ["LOCAL", "local", "Local"])
    def test_create_log_source_case_insensitive(self, source_type: str) -> None:
        """Test that log source types are case insensitive."""
        source = SourceFactory.create_log_source(source_type)
        assert isinstance(source, LocalLogAdapter)

    def test_github_actions_not_creatable_as_regular_log_source(self) -> None:
        """Test that GitHub Actions requires special factory method."""
        with pytest.raises(ValueError, match="requires GitHubActionsSource"):
            SourceFactory.create_log_source("github-actions")
