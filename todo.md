## The Project: "The Intelligent DevOps Incident Responder"

**The Business Problem:** When a production alert fires, a human usually has to manually check the logs, look at recent GitHub commits to see what changed, and then write a summary for the team. This takes 30 minutes of high-value engineering time.

**Your Goal:** Build a Multi-Agent system that triggers via an API and automatically researches a simulated "incident."

### 1. The Architecture (Multi-Agent)

Using **CrewAI**, you will define three distinct agents:

1. **The Log Analyst:** Uses a custom tool to "read" logs (a text file or mock API) and identifies the error pattern.
2. **The Code Historian:** Uses a tool to search a GitHub repo (or a local directory) for the last 3 commits in the affected service.
3. **The Incident Commander:** Takes the findings from the first two and writes a "Post-Mortem" report in Markdown, including a suggested fix.

### 2. The Technical Requirements

* **Backend:** Wrap the CrewAI execution in a **FastAPI** endpoint (`/trigger-investigation`).
* **Tools:** Write at least one **Custom Tool** for CrewAI. Don't just use built-in search; write a Python function that parses a local log file using Regex.
* **Validation:** Use **Pytest** to write a test case that ensures the final report contains specific keywords (e.g., "Error", "Commit", "Recommendation").
