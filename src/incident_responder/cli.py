"""Command-line interface for Incident Responder."""

import os
import sys
from datetime import datetime
from pathlib import Path

import click
import uvicorn

from src.incident_responder.constants import (
    DEFAULT_API_HOST,
    DEFAULT_API_PORT,
    DEFAULT_GIT_REPO_PATH,
    LOG_SOURCE_GITHUB_ACTIONS,
)
from src.incident_responder.sources import SourceFactory


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Incident Responder - AI-powered incident investigation tool."""
    pass


@cli.command()
@click.option(
    "--logs",
    type=click.Choice(["local", "github-actions", "datadog"], case_sensitive=False),
    default="local",
    help="Log source type",
)
@click.option(
    "--repo",
    type=str,
    help="Repository in format 'owner/repo' (for GitHub Actions)",
)
@click.option(
    "--run-url",
    type=str,
    help="GitHub Actions run URL (e.g., https://github.com/owner/repo/actions/runs/123456789)",
)
@click.option(
    "--run-id",
    type=int,
    help="GitHub Actions run ID",
)
@click.option(
    "--since",
    type=str,
    help="Start time for logs (ISO format: 2024-01-01T14:00:00)",
)
@click.option(
    "--until",
    type=str,
    help="End time for logs (ISO format: 2024-01-01T15:00:00)",
)
@click.option(
    "--git",
    type=click.Choice(["local", "github", "gitlab"], case_sensitive=False),
    default="local",
    help="Git source type",
)
@click.option(
    "--git-path",
    type=click.Path(exists=True),
    default=DEFAULT_GIT_REPO_PATH,
    help="Path to local git repository",
)
@click.option(
    "--github-token",
    type=str,
    envvar="GITHUB_TOKEN",
    help="GitHub personal access token (or set GITHUB_TOKEN env var)",
)
@click.option(
    "--output",
    type=click.Path(),
    help="Output file for the investigation report",
)
@click.option(
    "--service",
    type=str,
    default="app",
    help="Service name (for local log source)",
)
def investigate(
    logs: str,
    repo: str | None,
    run_url: str | None,
    run_id: int | None,
    since: str | None,
    until: str | None,
    git: str,
    git_path: str,
    github_token: str | None,
    output: str | None,
    service: str,
):
    """Investigate an incident using logs and git history."""
    click.echo("[SEARCHING] Starting incident investigation...")

    # Validate inputs
    if logs == LOG_SOURCE_GITHUB_ACTIONS:
        if not repo:
            click.echo("Error: --repo is required for GitHub Actions logs", err=True)
            sys.exit(1)
        if not run_url and not run_id and not (since and until):
            click.echo(
                "Error: Provide either --run-url/--run-id OR --since/--until for GitHub Actions",
                err=True,
            )
            sys.exit(1)

    # Parse time range
    since_dt = None
    until_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            click.echo(f"Error: Invalid --since format: {since}", err=True)
            sys.exit(1)
    if until:
        try:
            until_dt = datetime.fromisoformat(until.replace("Z", "+00:00"))
        except ValueError:
            click.echo(f"Error: Invalid --until format: {until}", err=True)
            sys.exit(1)

    # Get logs
    click.echo(f"[LOGS] Fetching from {logs}...")
    log_entries = []

    try:
        if logs == "github-actions":
            gh_source = SourceFactory.create_github_actions_source(
                token=github_token or os.environ.get("GITHUB_TOKEN")
            )

            if run_url or run_id:
                # Get specific run
                for entry in gh_source.get_workflow_logs(
                    repo, run_id=run_id, run_url=run_url
                ):
                    log_entries.append(entry)
                click.echo(
                    f"   Retrieved {len(log_entries)} log entries from workflow run"
                )
            elif since_dt and until_dt:
                # Get runs in time range
                for run in gh_source.get_workflow_runs(
                    repo, since=since_dt, until=until_dt
                ):
                    for entry in gh_source.get_workflow_logs(repo, run_id=run.id):
                        log_entries.append(entry)
                click.echo(
                    f"   Retrieved {len(log_entries)} log entries from time range"
                )

        elif logs == "local":
            log_source = SourceFactory.create_log_source("local")
            if since_dt and until_dt:
                for entry in log_source.get_logs(service, since_dt, until_dt):
                    log_entries.append(entry)
            click.echo(f"   Retrieved {len(log_entries)} log entries from local files")

    except Exception as e:
        click.echo(f"Error fetching logs: {e}", err=True)
        sys.exit(1)

    # Get git commits
    click.echo(f"[GIT] Fetching commits from {git}...")
    commits = []

    try:
        if git == "local":
            git_source = SourceFactory.create_git_source("local", repo_path=git_path)

            # Use the run's commit SHA if we have a GitHub run
            # Otherwise use time range
            for commit in git_source.get_commits(
                repo or "",
                since=since_dt,
                until=until_dt,
            ):
                commits.append(commit)

            click.echo(f"   Retrieved {len(commits)} commits")

    except Exception as e:
        click.echo(f"Error fetching commits: {e}", err=True)
        # Continue even if git fails

    # Format output
    click.echo("\n" + "=" * 50)
    click.echo("[REPORT] INVESTIGATION RESULTS")
    click.echo("=" * 50)

    click.echo(f"\n[LOGS] Log Entries: {len(log_entries)}")
    for entry in log_entries[:10]:  # Show first 10
        click.echo(f"   [{entry.level}] {entry.message[:80]}")

    if len(log_entries) > 10:
        click.echo(f"   ... and {len(log_entries) - 10} more")

    click.echo(f"\n[GIT] Git Commits: {len(commits)}")
    for commit in commits[:5]:  # Show first 5
        click.echo(f"   {commit.hash[:8]} - {commit.message[:60]}")

    if len(commits) > 5:
        click.echo(f"   ... and {len(commits) - 5} more")

    # Save to file if requested
    if output:
        output_path = Path(output)
        report = [
            "# Incident Investigation Report",
            "",
            f"**Date**: {datetime.now().isoformat()}",
            "",
            "## Log Entries",
            "",
        ]
        for entry in log_entries:
            report.append(f"- [{entry.level}] {entry.message}")

        report.extend(["", "## Git Commits", ""])
        for commit in commits:
            report.append(f"- {commit.hash[:8]} - {commit.message}")

        output_path.write_text("\n".join(report))
        click.echo(f"\n[SAVED] Report saved to: {output}")


@cli.command()
@click.option(
    "--host",
    type=str,
    default=DEFAULT_API_HOST,
    help="Host to bind the server to",
)
@click.option(
    "--port",
    type=int,
    default=int(DEFAULT_API_PORT),
    help="Port to bind the server to",
)
def serve(host: str, port: int):
    """Start the Incident Responder API server."""
    click.echo(f"[SERVER] Starting Incident Responder API server on {host}:{port}")
    click.echo(f"[INFO] API docs available at http://{host}:{port}/docs")

    # Import here to avoid loading FastAPI at CLI import time
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
        return {
            "name": API_TITLE,
            "version": API_VERSION,
            "status": "running",
            "docs": DOCS_URL,
        }

    uvicorn.run(app, host=host, port=port, log_level="info")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
