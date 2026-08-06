<div align="center">

# NeuroDebug

**Neuro-Symbolic AI Code Debugger**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-CI-2088FF.svg)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/joshi-chinmay-016/NeuroDebug)](https://github.com/joshi-chinmay-016/NeuroDebug/commits/main)
[![Stars](https://img.shields.io/github/stars/joshi-chinmay-016/NeuroDebug?style=social)](https://github.com/joshi-chinmay-016/NeuroDebug/stargazers)
[![Issues](https://img.shields.io/github/issues/joshi-chinmay-016/NeuroDebug)](https://github.com/joshi-chinmay-016/NeuroDebug/issues)
[![PRs](https://img.shields.io/github/issues-pr/joshi-chinmay-016/NeuroDebug)](https://github.com/joshi-chinmay-016/NeuroDebug/pulls)

**A production-grade AI-powered debugging platform that combines static AST analysis with dynamic execution verification**

[Live Demo](https://neuro-debug.vercel.app) • [Documentation](docs/) • [API Docs](docs/api.md) • [Architecture](docs/architecture.md) • [Roadmap](docs/roadmap.md) • [Report Bug](https://github.com/joshi-chinmay-016/NeuroDebug/issues) • [Request Feature](https://github.com/joshi-chinmay-016/NeuroDebug/issues)

</div>

---

## 🚀 Product Overview

NeuroDebug solves the fundamental problem of automated code debugging by combining the reliability of static analysis with the intelligence of large language models. Traditional debuggers either rely on static rule-based systems that miss complex errors, or purely LLM-based approaches that can hallucinate fixes without verification.

### Why Existing Debuggers Are Insufficient

- **Static Analysis Tools**: Fast but limited to predefined patterns, miss context-dependent bugs
- **Pure LLM Solutions**: Generate plausible but unverified fixes that may introduce new issues
- **Traditional Debuggers**: Require manual execution and breakpoint management, not automated

### Why NeuroDebug Exists

NeuroDebug introduces a neuro-symbolic approach that merges deterministic AST analysis with neural LLM reasoning, then validates every candidate patch through actual execution. This hybrid architecture ensures:

- **Deterministic Detection**: 13 static rules catch common Python errors with zero false positives
- **Contextual Understanding**: LLM analysis provides nuanced explanations for complex issues
- **Verified Fixes**: Every candidate patch is executed and tested before presentation
- **Structured Evidence**: Complete execution reports with stdout, stderr, and test results

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **Neuro-Symbolic Analysis** | Combines AST parsing with 13 deterministic rules for static error detection |
| **Candidate Patch Generation** | LLM-powered fix generation with syntax validation and diff visualization |
| **Execution Verification** | Isolated subprocess execution validates patches before presentation |
| **AST Rule Engine** | 13 static rules (R001-R013) covering syntax, undefined variables, anti-patterns |
| **Unified Diff Viewer** | Monaco Editor integration with syntax highlighting and side-by-side diff |
| **Secure Verification Pipeline** | Timeout-protected execution with structured evidence collection |
| **Structured Logging** | Request-scoped logging with pipeline stage timing and error tracking |
| **Modern UI** | React 19 with responsive design, dark/light themes, and smooth animations |
| **SaaS Foundation** | PostgreSQL persistence, session management, usage limiting, analytics |
| **Anonymous Access** | Guest users can debug without account creation |
| **Subscription Tiers** | Configurable Guest, Free, Pro, and Enterprise plans |

---

## 🏗️ System Architecture

### Overall Architecture

```mermaid
graph TD
    A[User Browser] --> B[React Frontend]
    B --> C[FastAPI Backend]
    C --> D[Session Manager]
    C --> E[Usage Engine]
    C --> F[Debug Service]
    F --> G[AST Parser]
    F --> H[Rule Engine]
    F --> I[Groq LLM Client]
    F --> J[Patch Generator]
    F --> K[Verification Engine]
    F --> L[Execution Layer]
    F --> M[Test Runner]
    F --> N[Diff Service]
    C --> O[PostgreSQL]
    C --> P[Repository Layer]
    C --> Q[Service Layer]
    
    style A fill:#e1f5ff
    style B fill:#fff4e1
    style C fill:#e8f5e9
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style F fill:#f3e5f5
    style G fill:#f3e5f5
    style H fill:#f3e5f5
    style I fill:#f3e5f5
    style J fill:#f3e5f5
    style K fill:#f3e5f5
    style L fill:#f3e5f5
    style M fill:#f3e5f5
    style N fill:#f3e5f5
    style O fill:#fce4ec
    style P fill:#d1c4e9
    style Q fill:#c8e6c9
```

### Database Schema

```mermaid
erDiagram
    subscription_plans ||--o{ subscription_limits : "has"
    subscription_plans ||--o{ users : "subscribes to"
    users ||--o{ projects : "owns"
    users ||--o{ usage_logs : "generates"
    users ||--o{ debug_sessions : "creates"
    projects ||--o{ debug_sessions : "contains"
    debug_sessions ||--o{ candidate_patches : "generates"
    debug_sessions ||--o{ verification_reports : "has"
    candidate_patches ||--o{ verification_reports : "verified by"

    subscription_plans {
        uuid id PK
        string tier
        integer daily_request_limit
        jsonb features
        boolean is_active
    }

    users {
        uuid id PK
        string email UK
        uuid subscription_plan_id FK
        timestamp last_login_at
    }

    debug_sessions {
        uuid id PK
        uuid user_id FK
        string session_id
        text code
        string error_type
    }

    usage_logs {
        uuid id PK
        uuid user_id FK
        string session_id
        timestamp request_timestamp
        string subscription_tier
    }
```

### Request Lifecycle

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Session
    participant Usage
    participant Pipeline
    participant LLM
    participant DB

    User->>Frontend: Submit Code
    Frontend->>API: POST /debug
    API->>Session: Get/Create Session
    Session->>DB: Query Session
    DB-->>Session: Session Data
    Session-->>API: Session ID + Tier
    API->>Usage: Check Rate Limit
    Usage->>DB: Query Daily Usage
    DB-->>Usage: Current Usage
    Usage-->>API: Limit Check
    API->>Pipeline: Execute Debug
    Pipeline->>Pipeline: AST Analysis
    Pipeline->>Pipeline: Rule Engine
    Pipeline->>LLM: Generate Analysis
    LLM-->>Pipeline: LLM Response
    Pipeline->>LLM: Generate Patch
    LLM-->>Pipeline: Candidate Patch
    Pipeline->>Pipeline: Verify Patch
    Pipeline-->>API: Debug Result
    API->>Usage: Record Usage
    Usage->>DB: Insert Usage Log
    API-->>Frontend: Response + Usage Info
    Frontend-->>User: Display Results
```

---

## 📦 Installation

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ (for local development without Docker)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/joshi-chinmay-016/NeuroDebug.git
cd NeuroDebug

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Seed database with subscription plans
python scripts/seed_database.py

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start development server
npm run dev
```

---

## 🔧 Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://neurodebug:neurodebug@localhost:5432/neurodebug
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Groq API
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Session
SESSION_EXPIRY_HOURS=24

# Usage Limits
DEFAULT_GUEST_LIMIT=3
DEFAULT_FREE_LIMIT=5
DEFAULT_PRO_LIMIT=20

# Logging
LOG_LEVEL=INFO
```

### Frontend Environment Variables

```bash
# API Configuration
VITE_API_URL=http://localhost:8000

# Firebase Configuration (optional)
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
```

---

## 💡 Usage

### Basic Debugging

```python
import requests

API_URL = "http://localhost:8000"

response = requests.post(
    f"{API_URL}/debug",
    json={
        "code": "def example():\n    return undefined_var",
        "api_key": "gsk_..."  # Optional
    }
)

result = response.json()
print(result["explanation"])
print(result["candidate_patch"]["patched_code"])
```

### With Verification

```python
response = requests.post(
    f"{API_URL}/verify",
    json={
        "original_code": "def example():\n    return undefined_var",
        "patched_code": "def example():\n    return None",
        "test_code": "def test_example():\n    assert example() is None"
    }
)

result = response.json()
print(result["verification_status"])
print(result["evidence"]["execution_comparison"])
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_debug_service.py
```

### Frontend Tests

```bash
cd frontend

# Run linting
npm run lint

# Run tests (when implemented)
npm test
```

---

## 📊 Subscription Tiers

| Feature | Guest | Free | Pro | Enterprise |
|---------|-------|------|-----|------------|
| Daily Requests | 3 | 5 | 20+ | Unlimited |
| AST Analysis | ✅ | ✅ | ✅ | ✅ |
| Rule Engine | ✅ | ✅ | ✅ | ✅ |
| LLM Analysis | ❌ | ✅ | ✅ | ✅ |
| Patch Generation | ❌ | ✅ | ✅ | ✅ |
| Verification | ❌ | ✅ | ✅ | ✅ |
| Projects | 0 | 3 | Unlimited | Unlimited |
| History | ❌ | ✅ | ✅ | ✅ |
| API Access | ❌ | ❌ | ✅ | ✅ |
| Priority Processing | ❌ | ❌ | ✅ | ✅ |
| Team Features | ❌ | ❌ | ❌ | ✅ |

---

## 📁 Project Structure

```
NeuroDebug/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── database/             # Database models and configuration
│   │   ├── base.py          # Base classes and mixins
│   │   ├── models.py        # SQLAlchemy models
│   │   └── __init__.py      # Database session management
│   ├── repositories/         # Repository pattern implementation
│   │   ├── base.py          # Base repository
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   └── ...
│   ├── routes/               # API route handlers
│   │   └── debug.py
│   ├── services/             # Business logic layer
│   │   ├── debug_service.py
│   │   ├── session_service.py
│   │   ├── usage_limit_service.py
│   │   └── ...
│   ├── analysis/             # AST analysis
│   ├── llm/                  # LLM integration
│   ├── models/               # Pydantic models
│   ├── tests/                # Backend tests
│   ├── scripts/              # Utility scripts
│   ├── main.py               # Application entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Projects.jsx
│   │   │   ├── History.jsx
│   │   │   ├── Analytics.jsx
│   │   │   ├── Pricing.jsx
│   │   │   ├── Settings.jsx
│   │   │   └── ...
│   │   ├── contexts/         # React contexts
│   │   ├── lib/              # Utility functions
│   │   ├── App.jsx           # Main application
│   │   └── main.jsx          # Entry point
│   ├── public/               # Static assets
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── docs/                     # Documentation
│   ├── architecture.md
│   ├── database.md
│   ├── deployment.md
│   ├── api.md
│   └── roadmap.md
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline
├── docker-compose.yml        # Docker orchestration
└── README.md
```

---

## 🛠️ Development Workflow

### Git Workflow

1. Create a feature branch from `main`
2. Implement your changes
3. Run tests and linting
4. Commit with conventional commits
5. Push and create a pull request
6. Ensure CI passes
7. Request review and merge

### Conventional Commits

```
feat: add user authentication
fix: resolve session management bug
docs: update API documentation
style: format code with black
refactor: improve repository pattern
test: add integration tests
chore: update dependencies
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution

- Additional language support
- Custom rule templates
- UI component improvements
- Documentation enhancements
- Bug fixes
- Performance improvements
- Test coverage

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Groq** for providing the LLM API
- **FastAPI** for the excellent web framework
- **React** for the amazing UI library
- **PostgreSQL** for the robust database
- All contributors and early adopters

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/joshi-chinmay-016/NeuroDebug/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joshi-chinmay-016/NeuroDebug/discussions)
- **Email**: support@neurodebug.com

---

## 🗺️ Roadmap

Check our [Roadmap](docs/roadmap.md) for upcoming features and planned improvements.

### Upcoming Features

- [ ] Firebase Auth integration
- [ ] Real-time analytics dashboard
- [ ] Team collaboration features
- [ ] API access and webhooks
- [ ] Mobile applications
- [ ] Multi-language support

---

<div align="center">

**Built with ❤️ for developers who demand excellence**

[⭐ Star us on GitHub](https://github.com/joshi-chinmay-016/NeuroDebug) • [🐦 Follow us on Twitter](https://twitter.com/neurodebug) • [💬 Join our Discord](https://discord.gg/neurodebug)

</div>
