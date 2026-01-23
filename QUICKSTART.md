# Quick Reference Guide

## 🚀 Start the Application

```bash
# Option 1: Using main.py
python main.py

# Option 2: Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Run Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_tools.py -v

# Specific test
pytest tests/test_api.py::TestHealthEndpoint::test_health_check_returns_200
```

## 🔧 API Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Trigger Investigation
```bash
curl -X POST "http://localhost:8000/api/v1/trigger-investigation" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "payment-service",
    "alert_type": "database_timeout",
    "timestamp": "2026-01-23T14:23:45.123"
  }'
```

### Get Investigation Status
```bash
# Replace {id} with actual investigation ID
curl http://localhost:8000/api/v1/investigation/{id}
```

## 📝 Configuration

Edit `.env` file:

```env
# LLM Settings
OLLAMA_MODEL=qwen3-coder
OLLAMA_BASE_URL=http://localhost:11434

# Paths
LOG_DIRECTORY=./data/logs
REPORTS_DIRECTORY=./reports
GIT_REPO_PATH=./data/mock_repo

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

## 🤖 Ollama Setup

```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the model
ollama pull qwen3-coder

# Start Ollama server
ollama serve
```

## 📊 Test with Mock Data

The project includes:
- **Mock Logs**: `data/logs/payment-service.log`
- **Mock Git Repo**: `data/mock_repo/`

### View Mock Logs
```bash
cat data/logs/payment-service.log
```

### View Mock Commits
```bash
cd data/mock_repo && git log --oneline
```

## 🛠️ Development

### Add a New Agent

1. Edit `src/incident_responder/config/agents.yaml`
2. Add method in `src/incident_responder/crew.py`:
   ```python
   @agent
   def my_agent(self) -> Agent:
       return Agent(config=self.agents_config['my_agent'], llm=self.llm)
   ```

### Add a New Tool

1. Create `src/incident_responder/tools/my_tool.py`
2. Implement `BaseTool` interface
3. Add to agent's tools list in `crew.py`

### Add a New Task

1. Edit `src/incident_responder/config/tasks.yaml`
2. Add method in `src/incident_responder/crew.py`:
   ```python
   @task
   def my_task(self) -> Task:
       return Task(config=self.tasks_config['my_task'], agent=self.my_agent())
   ```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **README**: [README.md](README.md)
- **Implementation**: [IMPLEMENTATION.md](IMPLEMENTATION.md)

## 🐛 Debugging

### Check Logs
```bash
# API logs are printed to stdout
python main.py

# Or with more detail
uvicorn main:app --reload --log-level debug
```

### Test Individual Tools
```bash
python -c "
from src.incident_responder.tools import LogParserTool
tool = LogParserTool()
result = tool._run('payment-service', '2026-01-23T14:00:00')
print(result)
"
```

### Verify Configuration
```python
python -c "
from src.incident_responder.utils.config import Config
print(f'LLM Model: {Config.OLLAMA_MODEL}')
print(f'Log Dir: {Config.LOG_DIRECTORY}')
print(f'Git Repo: {Config.GIT_REPO_PATH}')
"
```

## 🔍 Common Issues

### Issue: "Module not found"
**Solution**: Ensure you're in the project root and run:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: "Ollama connection refused"
**Solution**: Start Ollama server:
```bash
ollama serve
```

### Issue: "Log file not found"
**Solution**: Check LOG_DIRECTORY in `.env` points to correct path

### Issue: "Git repository not found"
**Solution**: Check GIT_REPO_PATH in `.env` or reinitialize:
```bash
cd data/mock_repo && git init
```

## 📦 Dependencies

Main packages:
- `crewai` - Multi-agent orchestration
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-dotenv` - Environment management
- `pytest` - Testing framework

## 🎯 Next Steps

1. ✅ Test the API with mock data
2. ✅ Run the test suite
3. 🔄 Customize agents/tasks for your use case
4. 🔄 Add your own log files
5. 🔄 Connect to real git repositories
6. 🔄 Deploy to production

---

**Need Help?** Check [README.md](README.md) for detailed documentation.
