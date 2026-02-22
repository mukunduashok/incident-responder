"""Local file-based log source adapter."""

import re
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

from ..constants import (
    LOG_FILE_EXTENSION,
    LOG_LEVEL_WARNING,
)
from ..utils.config import Config
from . import LogEntry, LogSource


def _normalize_datetime(dt: datetime) -> datetime:
    """Convert datetime to timezone-aware UTC for comparison."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


# Log format patterns (compiled for performance)
_LOG_PATTERNS = [
    # ISO format with level: 2024-01-01T14:30:00Z [ERROR] message
    re.compile(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)\s+\[?(\w+)\]?\s+(.*)"),
    # Simple format: 2024-01-01 14:30:00 ERROR message
    re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(\w+)\s+(.*)"),
]


class LocalLogAdapter(LogSource):
    """Adapter for reading logs from local files."""

    def __init__(
        self,
        log_directory: Path | None = None,
    ):
        """
        Initialize the local log adapter.

        Args:
            log_directory: Directory containing log files (default: from Config)
        """
        self.log_directory = log_directory or Config.LOG_DIRECTORY
        if isinstance(self.log_directory, str):
            self.log_directory = Path(self.log_directory)

    def _get_log_file_path(self, service: str) -> Path:
        """Get the log file path for a service."""
        return self.log_directory / f"{service}{LOG_FILE_EXTENSION}"

    def get_logs(
        self,
        service: str,
        since: datetime,
        until: datetime,
        level: str | None = None,
    ) -> Iterator[LogEntry]:
        """
        Get log entries for a service from local files.

        Args:
            service: Service name (used as filename)
            since: Start time for logs
            until: End time for logs
            level: Filter by log level

        Yields:
            LogEntry objects
        """
        log_file = self._get_log_file_path(service)

        if not log_file.exists():
            return

        # Normalize time range to timezone-aware UTC
        since_utc = _normalize_datetime(since)
        until_utc = _normalize_datetime(until)

        with open(log_file) as f:
            for line in f:
                entry = self._parse_log_line(line)
                if entry is None:
                    continue

                # Normalize entry timestamp for comparison
                entry_utc = _normalize_datetime(entry.timestamp)

                # Filter by time range
                if entry_utc < since_utc or entry_utc > until_utc:
                    continue

                # Filter by level
                if level and entry.level != level:
                    continue

                yield entry

    def _parse_log_line(self, line: str) -> LogEntry | None:
        """Parse a single log line into a LogEntry."""
        line = line.strip()
        if not line:
            return None

        for pattern in _LOG_PATTERNS:
            match = pattern.match(line)
            if match:
                timestamp_str, level, message = match.groups()
                timestamp = self._parse_timestamp(timestamp_str)
                level = self._normalize_level(level)

                return LogEntry(
                    timestamp=timestamp,
                    level=level,
                    message=message.strip(),
                    metadata={},
                    source="local",
                )

        # If no pattern matches, return as INFO
        return LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message=line,
            metadata={},
            source="local",
        )

    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime."""
        # Try ISO format first
        try:
            return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        # Try simple format
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # Fallback to current time
        return datetime.now()

    def _normalize_level(self, level: str) -> str:
        """Normalize log level to standard values."""
        level = level.upper()
        if level == "WARN":
            level = LOG_LEVEL_WARNING
        return level
