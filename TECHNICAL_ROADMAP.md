# Technical Roadmap - Incident Responder

> See **PRODUCT_ROADMAP.md** for product strategy and architecture decisions.

## Priority Improvements

### 1. Structured Logging
**Why**: Immediate value - helps debug issues, understand agent behavior, and trace failures. Quick to implement.

### 2. Retry Logic & Error Handling
**Why**: Agents fail often (LLM timeouts, API issues). Makes the system resilient without major architecture changes.

### 3. API Authentication
**Why**: Critical for production - currently anyone can trigger investigations. Simple API key middleware solves this.

---

## All Improvements

### Infrastructure & Production Readiness

| Improvement | Description |
|-------------|-------------|
| **Database for investigations** | Replace in-memory `dict` with PostgreSQL or Redis for persistence |
| **Authentication** | Add API keys, OAuth2, or JWT token-based auth |
| **Rate limiting** | Prevent abuse with slowapi or similar |
| **Celery/Redis queue** | Replace background tasks with proper task queue for reliability |
| **Deployment** | Add Docker, Kubernetes manifests, or docker-compose |

### Observability

| Improvement | Description |
|-------------|-------------|
| **Structured logging** | Use `structlog` or `loguru` with JSON format |
| **Metrics** | Add Prometheus metrics for API calls, agent execution times |
| **Tracing** | Add OpenTelemetry for distributed tracing |
| **Alerting** | Integrate with PagerDuty, Slack for failures |

### Agent & Tool Enhancements

| Improvement | Description |
|-------------|-------------|
| **Parallel agent execution** | Use `Process.hierarchical` instead of sequential |
| **Source adapters** | Implement GitHub, GitLab, Bitbucket adapters (see PRODUCT_ROADMAP.md) |
| **Log source adapters** | Implement Datadog, CloudWatch, ELK adapters (see PRODUCT_ROADMAP.md) |
| **Tool retry logic** | Add exponential backoff for failed tool calls |
| **Caching** | Cache git logs and log file reads |

### Error Handling & Resilience

| Improvement | Description |
|-------------|-------------|
| **Retry logic** | Add retry for LLM calls and external APIs |
| **Circuit breakers** | Prevent cascade failures |
| **Input validation** | Add more robust Pydantic validation |
| **Graceful degradation** | Continue with partial results if one agent fails |

### Configuration & Flexibility

| Improvement | Description |
|-------------|-------------|
| **Config management** | Use Pydantic Settings or Dynaconf |
| **Environment-specific configs** | Dev/staging/production configs |
| **Dynamic agent selection** | Choose agents based on alert type |

---

## Testing

| Improvement | Description |
|-------------|-------------|
| **Integration tests** | Test full API flow |
| **Mock LLM responses** | Use `responses` or `pytest-httpx` |
| **Contract testing** | Verify API contracts |
| **Load testing** | Add locust or k6 tests |

### Code Quality

| Improvement | Description |
|-------------|-------------|
| **Type hints** | Add more comprehensive typing |
| **Error code standardization** | Consistent error response format |
| **API versioning** | Plan for v2 API |

---

## External Integrations

> See **PRODUCT_ROADMAP.md** for data source adapter architecture and implementation details.
