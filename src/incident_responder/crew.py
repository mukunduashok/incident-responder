"""Incident Responder Crew - Multi-Agent orchestration for incident analysis."""

from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from .tools import GitSearchTool, LogParserTool, ReportGeneratorTool
from .utils.config import Config


@CrewBase
class IncidentResponderCrew:
    """
    Incident Responder Crew.

    A multi-agent system that analyzes production incidents by:
    1. Parsing logs for error patterns (Log Analyst)
    2. Searching git commits for recent changes (Code Historian)
    3. Generating comprehensive post-mortem reports (Incident Commander)
    """

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _get_llm(self):
        """Get LLM configuration for agents."""
        return LLM(
            model=f"azure_openai/{Config.AZURE_DEPLOYMENT_NAME}",
            api_key=Config.AZURE_API_KEY,
            api_base=Config.AZURE_API_BASE,
            api_version=Config.AZURE_API_VERSION,
            temperature=0.3,
        )

    @agent
    def log_analyst(self) -> Agent:
        """
        Log Analyst Agent.

        Specializes in parsing log files, identifying error patterns,
        and extracting timeline information.
        """
        return Agent(
            config=self.agents_config["log_analyst"],
            llm=self._get_llm(),
            tools=[LogParserTool()],
        )

    @agent
    def code_historian(self) -> Agent:
        """
        Code Historian Agent.

        Specializes in searching git history, analyzing commits,
        and identifying risky code changes.
        """
        return Agent(
            config=self.agents_config["code_historian"],
            llm=self._get_llm(),
            tools=[GitSearchTool()],
        )

    @agent
    def incident_commander(self) -> Agent:
        """
        Incident Commander Agent.

        Synthesizes findings from other agents and generates
        comprehensive post-mortem reports.
        """
        return Agent(
            config=self.agents_config["incident_commander"],
            llm=self._get_llm(),
            tools=[ReportGeneratorTool()],
        )

    @task
    def analyze_logs(self) -> Task:
        """Task for analyzing logs and identifying errors."""
        return Task(
            config=self.tasks_config["analyze_logs"],
            agent=self.log_analyst(),
        )

    @task
    def search_commits(self) -> Task:
        """Task for searching recent git commits."""
        return Task(
            config=self.tasks_config["search_commits"],
            agent=self.code_historian(),
        )

    @task
    def generate_postmortem(self) -> Task:
        """Task for generating the post-mortem report."""
        return Task(
            config=self.tasks_config["generate_postmortem"],
            agent=self.incident_commander(),
        )

    @crew
    def crew(self) -> Crew:
        """
        Creates the Incident Responder crew.

        Returns:
            Configured crew with all agents and tasks in sequential order
        """
        return Crew(
            agents=self.agents,  # Automatically populated by @agent decorators
            tasks=self.tasks,  # Automatically populated by @task decorators
            process=Process.sequential,  # Tasks execute in order
            verbose=True,
        )
