"""Custom tool for generating post-mortem reports."""

from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

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

            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"postmortem_{investigation_id}_{timestamp}.md"
            report_path = Config.REPORTS_DIRECTORY / filename

            # Add metadata header to report
            header = f"""---
Investigation ID: {investigation_id}
Generated: {datetime.now().isoformat()}
---

"""
            full_content = header + content

            # Save report
            with open(report_path, "w") as f:
                f.write(full_content)

            return f"Report successfully saved to: {report_path}"

        except Exception as e:
            return f"Error generating report: {str(e)}"
