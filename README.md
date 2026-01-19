# 🚀 DAALAB - Algorithm Analysis Platform

A comprehensive platform for secure code execution, algorithm analysis, and AI-powered code assistance. Features **Docker-based isolated code execution**, Supabase authentication with ES256 JWT, and a LangChain-powered AI assistant microservice.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Table of Contents

- [Overview](#overview)
- [Docker Container Execution](#-docker-container-execution-architecture)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Security](#-security)
- [Technology Stack](#-technology-stack)
- [Contributing](#-contributing)

## Overview

DAALAB enables users to write, execute, and analyze algorithms in a secure, isolated environment. The platform's core innovation is its **Docker-based code execution system**, ensuring that user-submitted code runs in complete isolation from the host system.

### Key Capabilities

- ✅ **Secure Code Execution**: Python and C++ code runs in isolated Docker containers
- ✅ **Real-time Performance Tracking**: Millisecond-precision runtime measurements
- ✅ **AI-Powered Analysis**: LangChain agents provide intelligent code reviews
- ✅ **Multi-Language Support**: Python 3.13 and C++17
- ✅ **User Authentication**: ES256 JWT-based secure authentication
- ✅ **Performance Visualization**: Interactive charts and analytics
- ✅ **Microservices Architecture**: Independent scalability for AI and execution services

## 🐳 Docker Container Execution Architecture

The platform's security and reliability are built on Docker containerization. Here's how code execution works:

### Execution Flow

```
User Code → API Server → Docker Container → Isolated Execution → Results → Container Destroyed
```

### Python Code Execution

**Container Configuration**:
- **Image**: `python:3.13-slim` (official Python slim image)
- **Isolation**: Each execution runs in a fresh, isolated container
- **Volume Mount**: User code mounted at `/code/code.py`
- **Auto-Cleanup**: Containers automatically removed after execution

**Implementation** ([container_runner.py](container_runner.py)):
```python
container = self.client.containers.run(
    "python:3.13-slim",
    command=["python", "-u", "/code/code.py"],
    volumes={code_path: {"bind": "/code/code.py", "mode": "rw"}},
    remove=True  # Automatic cleanup
)
```

### C++ Code Execution

**Container Configuration**:
- **Image**: `gcc:latest` (official GCC compiler)
- **Two-Phase Process**: Compilation → Execution
- **Standard**: C++17 support
- **Compile-Only Mode**: Available for syntax checking

**Implementation**:
```python
command=["sh", "-c", "g++ -std=c++17 -o /code/program /code/user.cpp && /code/program"]
```

### Security Benefits

| Benefit | Description |
|---------|-------------|
| **Complete Isolation** | Code cannot access host filesystem or network |
| **No Persistence** | Each execution starts with a clean state |
| **Resource Control** | Docker enforces CPU and memory limits |
| **Automatic Cleanup** | Containers destroyed immediately after use |
| **Consistent Environment** | Same execution environment for all users |
| **Multi-Tenancy Safe** | Concurrent executions are completely isolated |

### Fallback Mechanism

The system includes a **SafeCodeRunner** ([code_runner.py](code_runner.py)) with intelligent fallback:

1. **Primary**: Docker container execution (most secure)
2. **Fallback**: Local execution with restrictions if Docker unavailable
   - Blacklisted modules: `os`, `sys`, `subprocess`, `socket`, etc.
   - Forbidden functions: `eval`, `exec`, `open`, etc.
   - 10-second timeout enforcement
   - Dangerous pattern detection

## 🏗️ System Architecture

### Microservices Design

The platform uses a **2-microservice architecture** for scalability:

```
┌─────────────────────────────────────────────────────────┐
│                      User Browser                        │
│              (HTML/CSS/JS Frontend)                      │
└────────────┬────────────────────────────────────────────┘
             │
             │ HTTP/HTTPS
             │
    ┌────────▼─────────────────────────────────────┐
    │   Main API Service (Port 8000)               │
    │   - Code execution via Docker                │
    │   - Authentication (ES256 JWT)               │
    │   - Database operations                      │
    │   - Performance tracking                     │
    │   - Static file serving                      │
    └────────┬────────────────────┬─────────────────┘
             │                    │
             │                    │ HTTP
             │                    │
    ┌────────▼────────┐    ┌─────▼──────────────────┐
    │  Docker Engine  │    │ AI Service (Port 8001) │
    │  - Python       │    │ - LangChain agents     │
    │  - C++ (GCC)    │    │ - Code analysis        │
    │  - Containers   │    │ - Bug detection        │
    └─────────────────┘    │ - AI chat              │
                           └────────────────────────┘
             │
             │
    ┌────────▼────────┐
    │   Supabase      │
    │   - PostgreSQL  │
    │   - Auth        │
    │   - Storage     │
    └─────────────────┘
```

### Main API Service ([api_server.py](api_server.py))

**Port**: 8000  
**Framework**: FastAPI  
**Responsibilities**:
- Docker container orchestration for code execution
- User authentication and authorization
- Algorithm runtime data collection
- Performance analytics
- Frontend static file serving

**Key Endpoints**:
- `POST /api/run-code` - Execute Python code
- `POST /api/run-cpp` - Execute C++ code
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User authentication
- `GET /api/runtime-data` - Performance metrics

### AI Helper Service ([helper_agent/agent_service.py](helper_agent/agent_service.py))

**Port**: 8001  
**Framework**: FastAPI + LangChain  
**LLM**: Groq (Llama 3.3 70B Versatile)  
**Responsibilities**:
- Intelligent code analysis using LangChain agents
- Bug detection and security issue identification
- Code optimization suggestions
- Interactive conversational AI about code
- Complexity analysis

**Key Endpoints**:
- `POST /analyze` - Code analysis
- `POST /chat` - Interactive AI chat
- `GET /health` - Service health check
- `DELETE /session/{id}` - Clear conversation history

## ✨ Features

### Code Execution

- **Multi-Language Support**: Python 3.13 and C++17
- **Real-Time Output**: Instant execution results
- **Performance Metrics**: Millisecond-precision runtime tracking
- **Error Handling**: Comprehensive error reporting
- **Timeout Protection**: Prevents infinite loops

### AI-Powered Analysis

Powered by **LangChain agents** with specialized tools:

1. **Code Structure Analysis** ([tools.py](helper_agent/tools/tools.py))
   - AST parsing for Python
   - Function and class detection
   - Import analysis
   - Lines of code counting

2. **Issue Detection**
   - Security vulnerabilities (`eval`, `exec`)
   - Anti-patterns and code smells
   - Mutable default arguments
   - Bare except clauses
   - Style violations (PEP 8)

3. **Optimization Suggestions**
   - Performance improvements
   - Best practice recommendations
   - Refactoring opportunities

4. **Complexity Analysis**
   - Cyclomatic complexity
   - Cognitive complexity
   - Maintainability index

### User Management

- **Secure Authentication**: ES256 JWT tokens
- **User Profiles**: Personal code storage
- **Performance History**: Track algorithm runtimes
- **Session Management**: Conversation continuity

### Visualization

- **Runtime Graphs**: Interactive Plotly.js charts
- **Algorithm Comparison**: Side-by-side performance
- **Input Size Analysis**: Complexity visualization
- **Statistical Summaries**: Min, max, avg execution times

## 🔧 Installation

### Prerequisites

- **Python**: 3.9 or higher
- **Docker**: Installed and running
- **Supabase Account**: For authentication and database
- **Groq API Key**: For AI features (alternatively OpenAI)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd DAALAB
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment

Create a `.env` file in the root directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_JWKS_URL=https://your-project.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_KID=your-jwt-kid

# AI Service
GROQ_API_KEY=your-groq-api-key
AI_SERVICE_PORT=8001
AI_SERVICE_URL=http://localhost:8001

# Main Service
PORT=8000
HOST=0.0.0.0
```

### Step 4: Initialize Database

1. Open Supabase Dashboard → SQL Editor
2. Execute the schema from [docs/schema.sql](docs/schema.sql)

### Step 5: Pull Docker Images

```bash
docker pull python:3.13-slim
docker pull gcc:latest
```

## 🚀 Quick Start

### Option 1: PowerShell Script (Recommended for Windows)

```powershell
.\docs\start_services.ps1
```

### Option 2: Manual Start

**Terminal 1 - Main API Service**:
```bash
python api_server.py
```

**Terminal 2 - AI Helper Service**:
```bash
python -m helper_agent.agent_service
```

### Option 3: Using VS Code

1. Open integrated terminal
2. Split terminal (Ctrl+Shift+5)
3. Run services in separate terminals

### Access the Application

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **AI Service Docs**: http://localhost:8001/docs

## 📡 API Endpoints

### Main Service (Port 8000)

#### Code Execution

```http
POST /api/run-code
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "code": "print('Hello, World!')",
  "algorithm_name": "HelloWorld",
  "input_size": 1
}
```

```http
POST /api/run-cpp
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "code": "#include <iostream>\nint main() { std::cout << \"Hello\"; }",
  "algorithm_name": "CppHello",
  "input_size": 1
}
```

#### Authentication

```http
POST /api/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "username"
}
```

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

#### Analytics

```http
GET /api/runtime-data
Authorization: Bearer {jwt_token}
```

```http
GET /api/runtime-summary
Authorization: Bearer {jwt_token}
```

#### AI Integration

```http
POST /api/ai/analyze
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "code": "def example(): pass",
  "language": "python",
  "query": "Analyze this code"
}
```

### AI Service (Port 8001)

```http
POST /analyze
Content-Type: application/json

{
  "code": "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
  "language": "python",
  "query": "How can I optimize this?"
}
```

```http
POST /chat
Content-Type: application/json

{
  "question": "What's the time complexity?",
  "code": "for i in range(n): for j in range(n): print(i, j)",
  "session_id": "user-123"
}
```

## 🔒 Security

### Docker Container Isolation

- **No Host Access**: Containers cannot access the host filesystem beyond mounted files
- **Network Isolation**: No network access from containers
- **Resource Limits**: CPU and memory constraints enforced by Docker
- **Ephemeral Execution**: Containers destroyed immediately after use
- **Read-Only Mounts**: Where applicable, files are mounted read-only

### Authentication Security

- **ES256 JWT**: Elliptic Curve cryptographic signatures
- **JWKS Verification**: Public key fetched from Supabase
- **Token Validation**: Signature, audience, and expiration checks
- **Secure Storage**: Passwords hashed by Supabase Auth

### Code Safety (Fallback Mode)

When Docker is unavailable, the system enforces:
- Blacklist of dangerous modules (os, sys, subprocess, socket, etc.)
- Forbidden functions (eval, exec, open, etc.)
- Timeout enforcement (10 seconds max)
- Pattern detection for malicious code

### Best Practices

- CORS configured for specific origins in production
- Input validation via Pydantic models
- SQL injection prevention via Supabase client
- Error messages sanitized to prevent information leakage

## 🛠️ Technology Stack

### Backend

| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async web framework |
| **Docker SDK** | Container orchestration and management |
| **Supabase** | PostgreSQL database + authentication |
| **PyJWT** | ES256 JWT token verification |
| **LangChain** | AI agent framework for code analysis |
| **Groq** | Fast LLM inference (Llama 3.3 70B) |
| **Uvicorn** | ASGI server for FastAPI |
| **httpx** | Async HTTP client for microservice communication |

### Frontend

| Technology | Purpose |
|------------|---------|
| **Vanilla JavaScript** | No framework overhead |
| **HTML5/CSS3** | Modern responsive design |
| **Plotly.js** | Interactive data visualization |
| **Fetch API** | Async backend communication |

### Infrastructure

| Component | Details |
|-----------|---------|
| **Docker** | `python:3.13-slim`, `gcc:latest` images |
| **Supabase** | Managed PostgreSQL + Auth |
| **Microservices** | Independent service deployment |

## 📊 Database Schema

### Tables

#### `auth.users` (Managed by Supabase)
- User authentication data
- Password hashing
- Email verification

#### `algorithm_runtimes`
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key)
- algorithm_name: TEXT
- input_size: INTEGER
- execution_time_ms: NUMERIC
- code_snippet: TEXT
- output_result: TEXT
- created_at: TIMESTAMP
```

#### `user_code_files`
```sql
- id: UUID (primary key)
- user_id: UUID (foreign key)
- file_type: TEXT ('python' or 'cpp')
- code_content: TEXT
- filename: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
- UNIQUE(user_id, file_type)
```

## 🧪 Testing

### Test AI Service

```bash
python tests/test_ai_service.py
```

### Test with curl

**Analyze Code**:
```bash
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"world\")", "language": "python"}'
```

**Execute Python Code**:
```bash
curl -X POST http://localhost:8000/api/run-code \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"code": "print(2 + 2)"}'
```

## 📈 Performance

### Execution Times

- **Python Container Startup**: ~200-500ms
- **C++ Compilation + Execution**: ~500-1000ms
- **AI Analysis**: ~1-3 seconds (depending on code complexity)
- **JWT Verification**: <10ms

### Scalability

- **Concurrent Executions**: Unlimited (Docker manages resources)
- **AI Service**: Scales independently from main service
- **Database**: Supabase handles connection pooling
- **Stateless Design**: Easy horizontal scaling

## 🚀 Deployment

### Production Checklist

- [ ] Configure CORS with specific origins
- [ ] Set up environment variables securely
- [ ] Enable Docker resource limits
- [ ] Configure rate limiting
- [ ] Set up monitoring and logging
- [ ] Use Redis for session storage (replace in-memory)
- [ ] Deploy services independently
- [ ] Configure SSL/TLS certificates
- [ ] Set up backup strategy for database

### Recommended Hosting

- **Main API**: Railway, Render, or AWS ECS
- **AI Service**: Separate instance for independent scaling
- **Database**: Supabase (managed)
- **Docker**: Ensure Docker is available on hosting platform

## 🤝 Contributing

Contributions are welcome! This microservice architecture makes it easy to:

- Add new programming languages (just add Docker images)
- Extend AI analysis tools
- Swap LLM providers (replace Groq with OpenAI, Claude, etc.)
- Add new features to either service independently

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **Docker** for containerization technology
- **LangChain** for AI agent framework
- **Supabase** for authentication and database
- **Groq** for fast LLM inference

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in [docs/](docs/)
- Review API documentation at `/docs` endpoints

## 🔗 Related Documentation

- [AI Service Documentation](docs/AI_SERVICE_README.md)
- [Database Schema](docs/schema.sql)
- [Migration Guide](docs/DATABASE_MIGRATION_COMPLETE.md)
- [LangChain Documentation](https://python.langchain.com/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Built with ❤️ for secure, scalable code execution and AI-powered analysis**
