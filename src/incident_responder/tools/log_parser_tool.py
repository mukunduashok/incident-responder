"""Custom tool for parsing and analyzing log files."""

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from pathlib import Path

from ..utils.config import Config
from ..utils.log_utils import extract_errors_from_logs, parse_log_line


class LogParserInput(BaseModel):
    """Input schema for LogParserTool."""
    service_name: str = Field(..., description="Name of the service to analyze logs for")
    timestamp: str = Field(..., description="Timestamp to start analysis from (ISO format)")


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
    args_schema: Type[BaseModel] = LogParserInput
    
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
            log_file = Config.LOG_DIRECTORY / f"{service_name}.log"
            
            if not log_file.exists():
                return f"Error: Log file not found for service '{service_name}' at {log_file}"
            
            # Read log content
            with open(log_file, 'r') as f:
                log_content = f.read()
            
            # Extract and analyze errors
            analysis = extract_errors_from_logs(log_content)
            
            # Format output
            output = [
                f"=== Log Analysis for {service_name} ===\n",
                f"Analysis Period: Starting from {timestamp}",
                f"Total Errors Found: {analysis['total_errors']}",
                f"First Error Timestamp: {analysis['first_error_timestamp']}",
                f"\nAffected Services: {', '.join(analysis['affected_services'])}",
                f"\nError Types Distribution:"
            ]
            
            for error_type, count in analysis['error_types'].items():
                output.append(f"  - {error_type}: {count} occurrences")
            
            output.append("\nSample Error Messages (first 10):")
            for idx, error in enumerate(analysis['sample_errors'], 1):
                output.append(f"\n{idx}. [{error.timestamp}] {error.level} - {error.service}")
                output.append(f"   {error.message[:200]}...")  # Truncate long messages
            
            return "\n".join(output)
            
        except Exception as e:
            return f"Error parsing logs: {str(e)}"
