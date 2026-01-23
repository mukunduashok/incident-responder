# Incident Responder 🚨

An **Intelligent DevOps Multi-Agent System** that automatically investigates production incidents using CrewAI.

## 🎯 The Problem

When a production alert fires, engineers typically spend 30+ minutes manually:
- Checking logs for error patterns
- Reviewing recent GitHub commits
- Writing incident summaries for the team

## 💡 The Solution

This multi-agent system automates incident investigation via a REST API:

1. **Log Analyst Agent** - Parses logs using regex to identify errors
2. **Code Historian Agent** - Searches git commits for recent changes  
3. **Incident Commander Agent** - Generates comprehensive post-mortem reports

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         FastAPI REST API                │
│  POST /api/v1/trigger-investigation     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       CrewAI Multi-Agent System         │
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │   Log    │→ │   Code   │→ │Incident││
│  │ Analyst  │  │Historian │  │ Cmdr   ││
│  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
incident-responder/
├── src/incident_responder/
│   ├── config/
│   │   ├── agents.yaml          # Agent definitions
│   │   └── tasks.yaml           # Task definitions
│   ├── tools/
│   │   ├── log_parser_tool.py   # Custom regex log parser
│   │   ├── git_search_tool.py   # Git commit search
│   │   └── report_generator_tool.py
│   ├── api/
│   │   ├── routes.py            # FastAPI endpoints
│   │   └── models.py            # Pydantic models
│   ├── utils/
│   │   ├── config.py            # Configuration
│   │   └── log_utils.py         # Log parsing utilities
│   └── crew.py                  # CrewAI orchestration
├── data/
│   ├── logs/                    # Mock log files
│   └── mock_repo/               # Mock git repository
├── reports/                     # Generated post-mortems
├── tests/                       # Pytest test suite
└── main.py                      # Application entry point
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.12+
- Ollama installed and running (for local LLM)
- Git

### 2. Installation

```bash
# Clone the repository
git clone <repo-url>
cd incident-responder

# Install dependencies using uv
uv sync --all-groups

# Or with pip
pip install -e .
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# For Ollama (local):
OLLAMA_MODEL=qwen3-coder
OLLAMA_BASE_URL=http://localhost:11434
```

### 4. Start Ollama (if using local)

```bash
# Pull the model
ollama pull qwen3-coder

# Start Ollama server
ollama serve
```

### 5. Run the Application

```bash
# Start the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📖 Usage

### Trigger an Investigation

```bash
curl -X POST "http://localhost:8000/api/v1/trigger-investigation" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payment-service",
    "alert_type": "database_timeout",
    "timestamp": "2026-01-23T14:23:45.123"
  }'
```

Response:
```json
{
  "investigation_id": "abc-123-def-456",
  "status": "pending",
  "message": "Investigation started for payment-service",
  "report_path": "reports/postmortem_abc-123-def-456.md",
  "started_at": "2026-01-23T14:30:00.000"
}
```

### Check Investigation Status

```bash
curl "http://localhost:8000/api/v1/investigation/abc-123-def-456"
```

### Health Check

```bash
curl "http://localhost:8000/api/v1/health"
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_tools.py -v

# Run tests matching a pattern
pytest -k "test_log_parser"
```

## 🛠️ Development

### Design Principles

- **DRY (Don't Repeat Yourself)**: Shared utilities in `utils/`
- **Separation of Concerns**: Clear module boundaries
- **SOLID Principles**: Single-purpose tools and agents
- **Factory Pattern**: CrewAI's `@agent` and `@task` decorators
- **Strategy Pattern**: Pluggable tools for agents

### Adding a New Tool

1. Create tool class in `src/incident_responder/tools/`:

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(..., description="Parameter description")

class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "Tool description"
    args_schema: Type[BaseModel] = MyToolInput
    
    def _run(self, param: str) -> str:
        # Implementation
        return "result"
```

2. Add to agent in `config/agents.yaml`
3. Update tests in `tests/`

### Adding a New Agent

1. Define agent in `config/agents.yaml`
2. Add agent method in `crew.py` with `@agent` decorator
3. Create corresponding task in `config/tasks.yaml`
4. Add task method in `crew.py` with `@task` decorator

## 📊 Technical Requirements Met

✅ **Multi-Agent Architecture**: 3 specialized agents (Log Analyst, Code Historian, Incident Commander)  
✅ **FastAPI Backend**: `/trigger-investigation` endpoint  
✅ **Custom Tools**: Regex-based log parser implemented  
✅ **Pytest Validation**: Tests verify "Error", "Commit", "Recommendation" keywords  
✅ **CrewAI Integration**: Using `@CrewBase`, YAML configs, and LLM setup  

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_MODEL` | LLM model to use | `qwen3-coder` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `LOG_DIRECTORY` | Path to log files | `./data/logs` |
| `REPORTS_DIRECTORY` | Path to save reports | `./reports` |
| `GIT_REPO_PATH` | Path to git repository | `./data/mock_repo` |
| `API_HOST` | API server host | `0.0.0.0` |
| `API_PORT` | API server port | `8000` |

## 📝 Example Output

The system generates comprehensive post-mortem reports:

```markdown
# Post-Mortem Report

## Executive Summary
Database connection timeout errors occurred in payment-service.

## Timeline
- 14:23:45 - First ERROR detected in logs
- 14:23:50 - Database connection pool exhausted

## Root Cause Analysis
Recent Commit 9f6d43b reduced database timeout from 30s to 5s,
causing connections to fail under normal load.

## Recommendations
1. Revert timeout configuration to 30s
2. Add monitoring for database connection times
3. Implement gradual rollout for config changes
```

## 🚀 Production Considerations

- Replace in-memory `investigations` dict with Redis/PostgreSQL
- Add authentication/API keys
- Implement rate limiting
- Add monitoring and observability (Prometheus, Grafana)
- Use proper secrets management (Vault, AWS Secrets Manager)
- Add request validation and sanitization
- Implement circuit breakers for external services

## 📄 License

MIT License - see LICENSE file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

---

Built with ❤️ using [CrewAI](https://crewai.com) and [FastAPI](https://fastapi.tiangolo.com)
