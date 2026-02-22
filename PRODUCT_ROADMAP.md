# Product Roadmap - Incident Responder

## Vision

An AI-powered incident investigation platform that automatically correlates logs and code changes to help teams diagnose production issues faster.

---

## Product Architecture

### Core Insight: Abstraction is Key

The platform needs to work with multiple data sources without hardcoding each one. Use the **Adapter/Provider Pattern**:

```
┌─────────────────────────────────────────────────┐
│                 CrewAI Agents                    │
│   (Log Analyst, Code Historian, Commander)     │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│              Source Interface                   │
│   get_commits(repo, since, until)             │
│   get_logs(service, since, until, level)      │
└───────┬─────────────────────────────┬───────────┘
        │                             │
┌───────▼───────┐           ┌────────▼────────┐
│  GitHub Adapter│           │ Datadog Adapter │
│  GitLab Adapter│           │  ELK Adapter    │
│  BitBucket     │           │ Jenkins Adapter │
│  Local Git     │           │ CloudWatch       │
└───────────────┘           └─────────────────┘
```

---

## Data Source Abstraction

### Git Sources (Commit History)

All git sources provide the same core data:
- Commits (hash, author, date, message, diff)
- Branches and tags
- File history

| Source | Implementation | Status |
|--------|----------------|--------|
| **GitHub** | GitHub REST API | To implement |
| **GitLab** | GitLab API | To implement |
| **Bitbucket** | Bitbucket API | To implement |
| **Local Git** | GitPython/dulwich | ✅ Implemented |

### Log Sources

All log sources provide the same core data:
- Log entries (timestamp, level, message, metadata)
- Filtering by time range, severity, service

| Source | Implementation | Status |
|--------|----------------|--------|
| **Datadog** | Datadog Logs API | To implement |
| **Elasticsearch** | elasticsearch-py | To implement |
| **AWS CloudWatch** | boto3 | To implement |
| **Jenkins** | File-based / API | To implement |
| **GitHub Actions** | GitHub API | To implement |
| **Local Files** | File I/O | ✅ Implemented |

---

## Interface Definitions

### Git Source Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

@dataclass
class Commit:
    hash: str
    author: str
    date: datetime
    message: str
    diff: str | None = None

class GitSource(ABC):
    @abstractmethod
    def get_commits(
        self,
        repo: str,
        since: datetime | None = None,
        until: datetime | None = None,
        branch: str | None = None
    ) -> Iterator[Commit]:
        pass
```

### Log Source Interface

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator

@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    metadata: dict

class LogSource(ABC):
    @abstractmethod
    def get_logs(
        self,
        service: str,
        since: datetime,
        until: datetime,
        level: str | None = None
    ) -> Iterator[LogEntry]:
        pass
```

---

## Configuration

Sources are configured via YAML:

```yaml
# config/sources.yaml
git_sources:
  - type: github
    enabled: true
    config:
      owner: myorg
      repo: myapp
      token: ${GITHUB_TOKEN}
  - type: local
    enabled: false
    config:
      path: /path/to/repo

log_sources:
  - type: datadog
    enabled: true
    config:
      api_key: ${DATADOG_API_KEY}
      app_key: ${DATADOG_APP_KEY}
  - type: elasticsearch
    enabled: false
    config:
      hosts: ["http://localhost:9200"]
```

---

## Productization Paths

### Option 1: Python Package (Current Focus)

```
pip install incident-responder
```

**Best for:** Developers, self-hosted teams

| Pros | Cons |
|------|------|
| Fastest to ship | Limited enterprise features |
| Easy customization | Harder to monetize |
| Developer-friendly | Auth/scaling on them |

**Deliverables:**
- Clean pip-installable package
- YAML/TOML configuration
- CLI entry point (primary)
- FastAPI server (optional, for programmatic access)
- Docker image

**CLI Usage:**

```bash
# Option 1: Specific workflow run (recommended)
incident-responder investigate \
  --logs github-actions \
  --repo myorg/myapp \
  --run-url "https://github.com/myorg/myapp/actions/runs/123456789"

# Option 2: By run ID
incident-responder investigate \
  --logs github-actions \
  --repo myorg/myapp \
  --run-id 123456789

# Option 3: Time range (for broader investigation)
incident-responder investigate \
  --logs github-actions \
  --repo myorg/myapp \
  --since "2024-01-01 14:00" \
  --until "2024-01-01 15:00"

# With local git repo for code history
incident-responder investigate \
  --logs github-actions \
  --repo myorg/myapp \
  --run-id 123456789 \
  --git local \
  --git-path /path/to/repo

# Start optional API server
incident-responder serve --host 0.0.0.0 --port 8000
```

---

### Option 2: Hosted SaaS

**Best for:** Ops teams, enterprises

| Pros | Cons |
|------|------|
| Recurring revenue | Most complex to build |
| Handle auth/scaling | Multi-tenant isolation needed |
| OAuth integrations | 24/7 uptime responsibility |

**Deliverables:**
- Web API (FastAPI)
- OAuth (GitHub, GitLab, Datadog)
- Dashboard for investigations
- Webhook triggers from alerting

---

### Option 3: Hybrid

- Users install package → data syncs to your cloud
- SaaS for analysis/reporting
- Middle ground

---

## Implementation Priority

### Phase 1: CLI + GitHub Actions (Current)

- [ ] Add CLI entry point with `investigate` command
- [ ] Add `--logs`, `--repo`, `--since`, `--until` flags
- [ ] Implement GitHub Actions log source adapter
- [ ] Support reading from local git repo (already implemented)
- [ ] Config-driven source selection via `sources.yaml`

### Phase 2: Datadog Support

- [ ] Implement Datadog log source adapter
- [ ] Add Datadog configuration to sources.yaml

### Phase 3: Packaging

- [ ] Clean up package structure for PyPI
- [ ] Create Docker image
- [ ] Publish to Test PyPI

### Phase 4: Additional Sources

- [ ] Add more git sources (GitLab, Bitbucket)
- [ ] Add more log sources (CloudWatch, ELK, Jenkins)
- [ ] Add authentication (API keys)

### Phase 5: Scale (If SaaS)

- [ ] Multi-tenant isolation
- [ ] OAuth integrations
- [ ] Dashboard
- [ ] Webhook triggers

---

## Key Decisions to Make

1. **Go-to-market**: Self-hosted package first, or SaaS from day one?
2. **Pricing**: Per investigation? Per seat? Enterprise flat fee?
3. **Integration priority**: Which sources matter most for initial customers?
4. **Open core**: What features are free vs paid?

---

## Next Steps

1. Review this roadmap with potential users/customers
2. Prioritize which sources to implement first
3. Start with Phase 1: Foundation
