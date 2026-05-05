# NeuroDebug

A modern AI-powered code debugging platform that combines static AST analysis with dynamic visual effects and interactive components.

![NeuroDebug Demo Run](screenshots/demo_run_result.png)

---

## Features

### Core Functionality
- **AI-Powered Debug Analysis**: Combines static AST parsing with Groq LLM explanations
- **Interactive Code Editor**: Monaco Editor with syntax highlighting and real-time validation
- **Auto-Generated Tests**: Comprehensive pytest test cases from any Python code
- **Persistent History**: Firebase integration for storing and retrieving debug sessions
- **Modern UI/UX**: Responsive design with smooth animations and transitions

### Visual Effects & Components
- **Galaxy Background**: Interactive WebGL-based starfield with mouse repulsion effects
- **SplashCursor**: Fluid cursor effects with customizable particle trails
- **TextType Animation**: Smooth typing effects for dynamic text display
- **StarBorder Component**: Animated border effects for UI elements
- **BlurText Animation**: Letter-by-letter reveal animations
- **SaaS-Level Footer**: Professional footer with navigation and contact information

---

## How it works

### Debug Analysis Pipeline
```
User Code Input
    ↓
AST Parser (static analysis)
    ↓
Rule Engine (13 validation rules)
    ↓
Symbolic Layer (deterministic checks)
    ↓
Neural Layer (Groq LLM explanations)
    ↓
Enhanced Results → Frontend
```

### Frontend Architecture
```
React 18 + Vite
    ↓
Component-Based Design
    ↓
State Management (React Hooks)
    ↓
Real-time Updates
    ↓
Responsive Layout
```

---

## Project Structure
```
neurodebug/
├── backend/
│   ├── main.py           # FastAPI app — POST /debug
│   ├── parser.py         # AST analysis
│   ├── rules.py          # 13 static rules (R001–R013)
│   ├── llm_engine.py     # Groq LLM integration
│   ├── utils.py          # merge symbolic + neural results
│   ├── tests/
│   │   └── test_debug.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env              # your API key goes here
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── LandingPage.jsx    # Main landing page with all effects
│   │   │   ├── Debugger.jsx       # Code editor interface
│   │   │   ├── SaasFooter.jsx     # Professional footer component
│   │   │   ├── Galaxy.jsx          # WebGL galaxy background
│   │   │   ├── SplashCursorNew.jsx # Interactive cursor effects
│   │   │   ├── TextType.jsx        # Typing animation component
│   │   │   ├── StarBorder.jsx     # Animated border effects
│   │   │   └── BlurText.jsx       # Text reveal animations
│   │   ├── App.jsx       # Main app component
│   │   ├── main.jsx
│   │   └── index.css
│   ├── nginx.conf
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## UI Components

### Landing Page Features
- **Galaxy Background**: Interactive starfield with mouse-responsive particle effects
- **TextType Animation**: "Welcome to " typing effect above main title
- **BlurText Effects**: Animated "NeuroDebug" title reveal
- **StarBorder Developer Card**: Animated border around developer information
- **SaaS Footer**: Professional footer with navigation and contact links
- **Theme Support**: Dark/light mode toggle functionality.

### Interactive Elements
- **SplashCursor**: Fluid particle trail effects following mouse movement
- **Mouse Repulsion**: Galaxy stars react to cursor position
- **Responsive Design**: Adapts seamlessly to all screen sizes
- **Smooth Transitions**: Professional animations and micro-interactions
- sent as `api_key` in the POST body when they click "Run analysis"
- used to create a per-request Groq client — so **their account pays, not yours**

If no user key is provided, the backend falls back to the `GROQ_API_KEY` in `.env` (if set). If neither is set, the symbolic layer still runs — only the Groq explanation is skipped.

---

## Features

### Debug Analysis
- **Real-time feedback** on code errors
- **13 static rules** for common Python mistakes (see rules table below)
- **LLM-powered explanations** with corrected code suggestions
- **Confidence scoring** to show how certain the diagnosis is

### Test Generation
- **Auto-generate pytest test cases** for any Python code
- **Coverage includes**:
  - Happy path scenarios
  - Edge cases and boundary values
  - Error handling / exception cases
  - Type variations
- **Includes imports and setup code** ready to copy-paste
- **Customizable** — edit generated tests based on your requirements

---

## Static rules

| Rule | Category | Severity |
|------|----------|----------|
| R001 | SyntaxError | error |
| R002 | UndefinedVariable | error |
| R003 | ReturnOutsideFunction | error |
| R004 | BareExcept | warning |
| R005 | MutableDefaultArgument | warning |
| R006 | DivisionByZero | error |
| R007 | InfiniteLoop | warning |
| R008 | Python2Print | warning |
| R009 | NoneComparison | warning |
| R010 | BoolComparison | warning |
| R011 | ShadowedBuiltin | warning |
| R012 | SilentException | warning |
| R013 | UnusedImport | info | 

---

## Running locally

### Requirements
- Python 3.10+
- Node.js 18+

### Backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt

# optional — only needed if you want a server-side fallback key
cp .env.example .env
# edit .env and set GROQ_API_KEY=gsk-...

uvicorn main:app --reload --port 8000
```

API: `http://localhost:8000`
Swagger docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000`

### Tests

```bash
cd backend
pip install pytest
pytest tests/ -v
```

---

## Docker

```bash
# make sure backend/.env has GROQ_API_KEY (optional — users can supply their own)
docker-compose up --build
```

- Frontend → `http://localhost:3000`
- Backend  → `http://localhost:8000`

---

## API reference

### `POST /debug`

```json
// request
{
  "code": "x = undefined_var\nprint(x)",
  "api_key": "sk-..."   // optional — user's own key
}

// response
{
  "error_type": "UndefinedVariable",
  "explanation": "The name 'undefined_var' is used on line 1 but was never defined...",
  "suggested_fix": "x = 'some value'\nprint(x)",
  "confidence_score": 0.93,
  "symbolic_issues": [
    {
      "rule_id": "R002",
      "severity": "error",
      "category": "UndefinedVariable",
      "message": "Name 'undefined_var' is used but never defined in this snippet.",
      "line": null
    }
  ],
  "raw_errors": ["[R002] Name 'undefined_var' is used but never defined in this snippet."]
}
```

### `POST /generate-tests`

Generate pytest test cases for Python code.

```json
// request
{
  "code": "def add(a, b):\n    return a + b",
  "api_key": "gsk-..."   // optional — user's own key
}

// response
{
  "success": true,
  "test_cases": [
    {
      "test_name": "test_add_positive_numbers",
      "test_code": "def test_add_positive_numbers():\n    assert add(2, 3) == 5",
      "description": "Test adding two positive numbers"
    },
    {
      "test_name": "test_add_with_zero",
      "test_code": "def test_add_with_zero():\n    assert add(5, 0) == 5",
      "description": "Test adding with zero"
    }
  ],
  "imports": "import pytest",
  "setup_code": "",
  "error": null
}
```

### `GET /health`

```json
{ "status": "healthy", "service": "NeuroDebug API", "version": "1.0.0" }
```

---

## Deploying to AWS EC2

### 1. Launch instance

- AMI: Ubuntu 22.04 LTS
- Type: t2.medium (or t2.micro for free tier)
- Security group inbound rules:

  | Port | Source | Purpose |
  |------|--------|---------|
  | 22   | your IP | SSH |
  | 3000 | 0.0.0.0/0 | Frontend |
  | 8000 | 0.0.0.0/0 | Backend API |

### 2. SSH in

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 3. Install Docker

```bash
sudo apt-get update -y
sudo apt-get install -y docker.io

sudo curl -L \
  "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

sudo usermod -aG docker ubuntu
newgrp docker
```

### 4. Clone and configure

```bash
git clone https://github.com/your-username/neurodebug.git
cd neurodebug

# optional server-side fallback key
cat > backend/.env << EOF
GROQ_API_KEY=gsk-...
EOF
```

### 5. Run

```bash
docker-compose up --build -d

# check status
docker-compose ps

# view logs
docker-compose logs -f
```

### 6. Access

```
http://<EC2_PUBLIC_IP>:3000   ← app
http://<EC2_PUBLIC_IP>:8000   ← API
```

### Useful commands

```bash
docker-compose down               # stop
docker-compose restart backend    # restart one service
docker-compose up --build -d      # rebuild after code changes
docker exec -it neurodebug_backend bash   # shell into backend
```

---

## Tech

| | |
|-|--|
| Backend | FastAPI + Uvicorn |
| Analysis | Python `ast` module |
| AI | Groq Llama 3 |
| Frontend | React 18 + Vite |
| Editor | Monaco Editor |
| Serving | nginx |
| Containers | Docker + Docker Compose |
| Deployment | AWS EC2 (Ubuntu 22.04) |

---


---

## License

MIT
