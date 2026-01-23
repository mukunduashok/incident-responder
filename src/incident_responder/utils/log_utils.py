"""Log parsing utilities and patterns."""

import re
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LogEntry:
    """Represents a parsed log entry."""
    timestamp: str
    level: str
    service: str
    message: str
    raw_line: str


class LogPatterns:
    """Regex patterns for log parsing."""
    
    # Standard log format: 2026-01-23 14:23:45.123 ERROR [service-name] message
    STANDARD_LOG = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+'
        r'(?P<level>DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\s+'
        r'\[(?P<service>[^\]]+)\]\s+'
        r'(?P<message>.*)'
    )
    
    # Error patterns
    ERROR_KEYWORDS = re.compile(
        r'(error|exception|failed|failure|timeout|refused|cannot|unable|crashed|panic)',
        re.IGNORECASE
    )
    
    # Stack trace patterns
    STACK_TRACE = re.compile(
        r'(Traceback|Stack trace|^\s+at\s+|^\s+File\s+")',
        re.MULTILINE
    )
    
    # Common error types
    DATABASE_ERROR = re.compile(
        r'(database|sql|postgres|mysql|mongodb|connection.*timeout|deadlock)',
        re.IGNORECASE
    )
    
    HTTP_ERROR = re.compile(
        r'(http.*\d{3}|status.*[45]\d{2}|connection.*refused|timeout.*request)',
        re.IGNORECASE
    )
    
    NULL_POINTER = re.compile(
        r'(null.*pointer|none.*type|attribute.*error|key.*error)',
        re.IGNORECASE
    )


def parse_log_line(line: str) -> LogEntry | None:
    """Parse a single log line into a LogEntry."""
    match = LogPatterns.STANDARD_LOG.match(line)
    if match:
        return LogEntry(
            timestamp=match.group('timestamp'),
            level=match.group('level'),
            service=match.group('service'),
            message=match.group('message'),
            raw_line=line
        )
    return None


def categorize_error(message: str) -> List[str]:
    """Categorize error message into types."""
    categories = []
    
    if LogPatterns.DATABASE_ERROR.search(message):
        categories.append("Database")
    if LogPatterns.HTTP_ERROR.search(message):
        categories.append("HTTP/Network")
    if LogPatterns.NULL_POINTER.search(message):
        categories.append("NullPointer/Attribute")
    if LogPatterns.STACK_TRACE.search(message):
        categories.append("Exception/StackTrace")
    
    if not categories:
        categories.append("General")
    
    return categories


def extract_errors_from_logs(log_content: str) -> Dict:
    """Extract and analyze errors from log content."""
    lines = log_content.split('\n')
    errors = []
    error_counts = {}
    first_error_time = None
    affected_services = set()
    
    for line in lines:
        entry = parse_log_line(line)
        if entry and entry.level in ['ERROR', 'CRITICAL', 'FATAL']:
            errors.append(entry)
            affected_services.add(entry.service)
            
            # Track first error
            if first_error_time is None:
                first_error_time = entry.timestamp
            
            # Count error types
            categories = categorize_error(entry.message)
            for category in categories:
                error_counts[category] = error_counts.get(category, 0) + 1
    
    return {
        "total_errors": len(errors),
        "error_types": error_counts,
        "first_error_timestamp": first_error_time,
        "affected_services": list(affected_services),
        "sample_errors": errors[:10],  # First 10 errors
    }
