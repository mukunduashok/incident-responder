"""Custom tool for parsing and analyzing log files."""

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..constants import LOG_FILE_EXTENSION, MAX_ERROR_MESSAGE_LENGTH
from ..utils.config import Config
from ..utils.log_utils import extract_errors_from_logs


class LogParserInput(BaseModel):
    """Input schema for LogParserTool."""

    service_name: str = Field(
        ..., description="Name of the service to analyze logs for"
    )
    timestamp: str = Field(
        ..., description="Timestamp to start analysis from (ISO format)"
    )


class LogParserTool(BaseTool):
    """
    Custom tool for parsing log files using regex patterns.

    This tool reads log files for a specified service and extracts error patterns,
    stack traces, affected components, and timeline information.
    """

    name: str = "log_parser"
    description: str = (
        "Parses log files for a specific service to identify errors, exceptions, "
        "and anomalies. Returns structured information about error types, frequencies, "
        "affected components, and timeline of when errors started occurring. "
        "Input should include service_name and timestamp."
    )
    args_schema: type[BaseModel] = LogParserInput

    def _run(self, service_name: str, timestamp: str) -> str:
        """
        Parse logs for the specified service.

        Args:
            service_name: Name of the service (e.g., 'payment-service')
            timestamp: Starting timestamp for analysis

        Returns:
            Structured analysis of log errors
        """
        try:
            # Find log file for the service
            log_file = Config.LOG_DIRECTORY / f"{service_name}{LOG_FILE_EXTENSION}"

            if not log_file.exists():
                return f"Error: Log file not found for service '{service_name}' at {log_file}"

            # Read log content
            with open(log_file) as f:
                log_content = f.read()

            # Extract and analyze errors
            analysis = extract_errors_from_logs(log_content)

            # Format output
            output = self._format_analysis_output(service_name, timestamp, analysis)

            return output

        except Exception as e:
            return f"Error parsing logs: {str(e)}"

    def _format_analysis_output(
        self, service_name: str, timestamp: str, analysis: dict
    ) -> str:
        """
        Format log analysis output.

        Args:
            service_name: Name of the service
            timestamp: Starting timestamp for analysis
            analysis: Analysis results dictionary

        Returns:
            Formatted string output
        """
        output = [
            f"=== Log Analysis for {service_name} ===\n",
            f"Analysis Period: Starting from {timestamp}",
            f"Total Errors Found: {analysis['total_errors']}",
            f"First Error Timestamp: {analysis['first_error_timestamp']}",
            f"\nAffected Services: {', '.join(analysis['affected_services'])}",
            "\nError Types Distribution:",
        ]

        for error_type, count in analysis["error_types"].items():
            output.append(f"  - {error_type}: {count} occurrences")

        output.append("\nSample Error Messages (first 10):")
        for idx, error in enumerate(analysis["sample_errors"], 1):
            output.append(
                f"\n{idx}. [{error.timestamp}] {error.level} - {error.service}"
            )
            # Truncate long messages
            truncated_message = error.message[:MAX_ERROR_MESSAGE_LENGTH]
            if len(error.message) > MAX_ERROR_MESSAGE_LENGTH:
                truncated_message += "..."
            output.append(f"   {truncated_message}")

        return "\n".join(output)
