"""Custom tool for generating post-mortem reports."""

import os
from datetime import datetime

from crewai.tools import BaseTool
from openai import AzureOpenAI
from pydantic import BaseModel, Field

from ..constants import (
    REPORT_FILENAME_EXTENSION,
    REPORT_FILENAME_PREFIX,
    REPORT_METADATA_SEPARATOR,
)
from ..utils.config import Config
from ..utils.qdrant_store import store_report_embedding


class ReportGeneratorInput(BaseModel):
    """Input schema for ReportGeneratorTool."""

    investigation_id: str = Field(..., description="Unique ID for this investigation")
    content: str = Field(
        ..., description="Content of the post-mortem report in Markdown format"
    )
    alert_type: str = Field(
        ..., description="Type of alert triggering the investigation"
    )
    service_name: str = Field(
        ..., description="Name of the service under investigation"
    )
    timestamp: str = Field(..., description="Timestamp of the alert or investigation")


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

    def _run(
        self,
        investigation_id: str,
        content: str,
        alert_type: str,
        service_name: str,
        timestamp: str,
    ) -> str:
        """
        Generate and save a post-mortem report.

        Args:
            investigation_id: Unique identifier for this investigation
            content: Report content in Markdown format
            alert_type: Type of alert
            service_name: Name of service
            timestamp: Alert/investigation timestamp

        Returns:
            Path where the report was saved
        """
        try:
            Config.REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
            filename = self._generate_filename(investigation_id)
            report_path = Config.REPORTS_DIRECTORY / filename
            header = self._generate_metadata_header(investigation_id)
            full_content = header + content
            with open(report_path, "w") as f:
                f.write(full_content)

            embedding = self._generate_embedding(full_content)
            store_report_embedding(
                investigation_id=investigation_id,
                alert_type=alert_type,
                service_name=service_name,
                report_path=str(report_path),
                embedding=embedding,
                timestamp=timestamp,
            )
            return f"Report successfully saved to: {report_path}"
        except Exception as e:
            return f"Error generating report: {str(e)}"

    def _generate_embedding(self, content: str) -> list:
        """
        Generate embedding for report content using Azure OpenAI.
        """
        api_key = os.getenv("AZURE_API_KEY", Config.AZURE_API_KEY)
        api_base = os.getenv("AZURE_EMBEDDING_ENDPOINT", Config.AZURE_API_BASE)
        api_version = os.getenv("AZURE_API_VERSION", Config.AZURE_API_VERSION)
        embedding_deployment = os.getenv(
            "AZURE_EMBEDDING_DEPLOYMENT", "embedding-3-small"
        )
        client = AzureOpenAI(
            api_key=api_key, azure_endpoint=api_base, api_version=api_version
        )
        embedding_response = client.embeddings.create(
            input=content,
            model=embedding_deployment,
        )
        return embedding_response.data[0].embedding

    def _generate_filename(self, investigation_id: str) -> str:
        """
        Generate report filename (one per investigation).

        Args:
            investigation_id: Unique investigation identifier

        Returns:
            Formatted filename
        """
        return f"{REPORT_FILENAME_PREFIX}_{investigation_id}{REPORT_FILENAME_EXTENSION}"

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
