"""Custom tool for generating post-mortem reports."""

from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from ..constants import (
    REPORT_FILENAME_EXTENSION,
    REPORT_FILENAME_PREFIX,
    REPORT_METADATA_SEPARATOR,
    REPORT_TIMESTAMP_FORMAT,
)
from ..utils.config import Config


class ReportGeneratorInput(BaseModel):
    """Input schema for ReportGeneratorTool."""

    investigation_id: str = Field(..., description="Unique ID for this investigation")
    content: str = Field(
        ..., description="Content of the post-mortem report in Markdown format"
    )


class ReportGeneratorTool(BaseTool):
    """
    Custom tool for generating and saving post-mortem reports.

    This tool formats and saves investigation reports in Markdown format.
    """

    name: str = "report_generator"
    description: str = (
        "Generates and saves a post-mortem report in Markdown format. "
        "Takes the investigation ID and report content, then saves it to a file. "
        "Returns the path where the report was saved. "
        "Input should include investigation_id and content (in Markdown)."
    )
    args_schema: type[BaseModel] = ReportGeneratorInput

    def _run(self, investigation_id: str, content: str) -> str:
        """
        Generate and save a post-mortem report.

        Args:
            investigation_id: Unique identifier for this investigation
            content: Report content in Markdown format

        Returns:
            Path where the report was saved
        """
        try:
            # Ensure reports directory exists
            Config.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

            # Create filename with timestamp
            filename = self._generate_filename(investigation_id)
            report_path = Config.REPORTS_DIRECTORY / filename

            # Add metadata header to report
            header = self._generate_metadata_header(investigation_id)
            full_content = header + content

            # Save report
            with open(report_path, "w") as f:
                f.write(full_content)

            return f"Report successfully saved to: {report_path}"

        except Exception as e:
            return f"Error generating report: {str(e)}"

    def _generate_filename(self, investigation_id: str) -> str:
        """
        Generate report filename with timestamp.

        Args:
            investigation_id: Unique investigation identifier

        Returns:
            Formatted filename
        """
        timestamp = datetime.now().strftime(REPORT_TIMESTAMP_FORMAT)
        return f"{REPORT_FILENAME_PREFIX}_{investigation_id}_{timestamp}{REPORT_FILENAME_EXTENSION}"

    def _generate_metadata_header(self, investigation_id: str) -> str:
        """
        Generate metadata header for the report.

        Args:
            investigation_id: Unique investigation identifier

        Returns:
            Formatted metadata header
        """
        return f"""{REPORT_METADATA_SEPARATOR}
Investigation ID: {investigation_id}
Generated: {datetime.now().isoformat()}
{REPORT_METADATA_SEPARATOR}

"""
