# 🚀 DAALAB - Algorithm Analysis Platform with AI

A comprehensive platform for algorithm visualization, code execution, and AI-powered code analysis. Features secure Docker-based code execution, Supabase authentication with ES256 JWT, and a LangChain-powered AI assistant microservice.

## 🌟 Features

### Core Features

- **🔒 Secure Execution**: Code runs in isolated Docker containers
- **⚡ Real-time Output**: See execution results and runtime immediately
- **🎨 Modern UI**: Beautiful, responsive interface
- **💾 Data Persistence**: Algorithm runtime tracking with Supabase
- **📊 Visualization**: Performance analysis and runtime comparisons
- **👤 User Authentication**: JWT-based auth with ES256 signing (updated from RS256)

### 🤖 AI Features (New!)

- **AI Code Analysis**: LangChain-powered intelligent code review
- **Bug Detection**: Automatic identification of issues and anti-patterns
- **Optimization Suggestions**: Performance and best practice recommendations
- **Interactive Chat**: Ask questions about your code
- **Microservice Architecture**: Independent AI service for scalability

## 🏗️ Architecture

The platform consists of **two microservices**:

1. **Main API Service** (Port 8000)
   - Code execution (Python & C++)
   - Authentication & authorization (ES256 JWT)
   - Database operations
   - Algorithm tracking
2. **AI Helper Service** (Port 8001)
   - LangChain agents with modern API
   - Code analysis tools
   - Natural language processing
   - Conversational AI

## 📋 Prerequisites

- Python 3.9+
- Docker installed and running
- Supabase account with ES256 JWT configuration
- OpenAI API key (for AI features)

## 🔧 Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd DAALAB
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install AI service dependencies:

```bash
cd code_assist
pip install -r requirements.txt
cd ..
```

4. Configure environment variables in `.env`:

```env
# Supabase Configuration
SUPABASE_URL=https://____.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_JWKS_URL=....
SUPABASE_JWT_KID=******
SUPERBASE_SERVICE_ROLE_KEY=...

# AI Service
GROQ_API_KEY_1=....
AI_SERVICE_PORT=8001
AI_SERVICE_URL=http://localhost:8001

# Main Service
PORT=8000
HOST=0.0.0.0
```

5. Initialize database:
   - Go to Supabase Dashboard → SQL Editor
   - Run the contents of `schema.sql`

## 🚀 Quick Start

**Terminal 1 - Main Service:**

```bash
uvicorn api_server:app
```

**Terminal 2 - AI Service:**

```bash
cd code_assist
python main.py
```

### Test AI Service

```bash
python test_ai_service.py
```

## 📚 Documentation

- **[AI Service Documentation](AI_SERVICE_README.md)** - Complete microservice guide
- **[Database Schema](schema.sql)** - ES256 JWT configuration
- **[API Endpoints](#-api-endpoints)** - See below

## 🔌 API Endpoints

### Main Service (http://localhost:8000)

#### Code Execution

```
POST /api/run-code       - Execute Python code
POST /api/run-cpp        - Execute C++ code
```

#### Authentication (ES256 JWT)

```
POST /api/auth/signup    - Create new user
POST /api/auth/login     - User login (returns ES256 JWT)
POST /api/auth/logout    - User logout
```

#### AI Integration (New!)

```
POST /api/ai/analyze     - Analyze code with AI
POST /api/ai/chat        - Interactive chat about code
GET  /api/ai/health      - Check AI service status
DELETE /api/ai/session/{id} - Clear conversation history
```

#### Data & Analytics

```
GET /api/runtime-data    - Get algorithm runtime data
GET /api/runtime-summary - Performance summary
GET /api/health          - Service health check
```

### AI Service (http://localhost:8001)

```
POST /analyze            - Direct code analysis
POST /chat               - Interactive AI chat
GET  /health             - Service health check
DELETE /session/{id}     - Clear session
```

## 🧪 Testing

### Test Main Service

```bash
# Health check
curl http://localhost:8000/api/health
```

### Test AI Service

```bash
# Health check
curl http://localhost:8001/health

# Analyze code
curl -X POST http://localhost:8001/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"world\")", "language": "python"}'
```

### Test Authentication

```bash
# Signup
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123", "username": "testuser"}'

# Login (returns ES256 JWT)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## 🔐 Security Updates

### ES256 JWT Migration

This platform has been updated from RS256 to ES256 JWT signing:

- **Algorithm**: ES256 (Elliptic Curve)
- **Key Type**: EC (P-256 curve)
- **JWKS**: Automatic public key fetching
- **Verification**: Full signature validation with PyJWT[crypto]

See [auth.py](auth.py) for implementation details.

## 🛠️ Tech Stack

### Backend

- **FastAPI** - Main API framework
- **LangChain** - AI agent framework
- **PyJWT** - ES256 JWT verification
- **Supabase** - Database & authentication
- **Docker** - Code execution containers
- **httpx** - Async HTTP client

### AI/ML

- **OpenAI GPT-4** - Language model
- **LangChain Tools** - Code analysis utilities
- **AST Parser** - Python code analysis

### Frontend

- HTML5, CSS3, JavaScript
- Plotly.js - Data visualization

## 📊 LangChain Tools

The AI service includes specialized tools:

1. **analyze_code_structure** - Extract functions, classes, imports
2. **detect_code_issues** - Find bugs, security issues, anti-patterns
3. **suggest_improvements** - Optimization recommendations
4. **calculate_complexity** - Cyclomatic complexity metrics

## 🌐 Deployment

### Production Configuration

1. **Separate Hosting**: Deploy services independently
2. **Environment Variables**: Use platform-specific secrets
3. **CORS**: Update allowed origins
4. **Scaling**: AI service scales independently
5. **Session Storage**: Replace in-memory with Redis

See [AI_SERVICE_README.md](AI_SERVICE_README.md) for detailed deployment guide.

## 🐛 Troubleshooting

### AI Service Not Available

```bash
# Check if service is running
curl http://localhost:8001/health

# Restart AI service
cd code_assist
python main.py
```

### Main Service Issues

```bash
# Check if service is running
curl http://localhost:8000/api/health

# Restart main service
uvicorn api_server:app --reload
```

### JWT Verification Errors

- Verify JWKS URL is correct
- Check Supabase project settings
- Ensure PyJWT[crypto] is installed

### Docker Issues

```bash
# Check Docker status
docker ps

# Pull Python image
docker pull python:3.9-slim
```

### Port Already in Use

```bash
# Kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

## 📁 Project Structure

```
DAALAB/
├── api_server.py           # Main FastAPI server
├── auth.py                 # ES256 JWT authentication
├── schema.sql              # Database schema
├── requirements.txt        # Main service dependencies
├── static/                 # Frontend files
│   ├── index.html
│   ├── styles.css
│   └── ...
└── code_assist/            # AI service (separate microservice)
    ├── main.py             # AI service entry point
    ├── requirements.txt    # AI service dependencies
    └── ...
```

## 📈 Future Enhancements

- [ ] Support for more programming languages
- [ ] Code diff and version comparison
- [ ] Team collaboration features
- [ ] Advanced AI models (Claude, Llama)
- [ ] Redis session management
- [ ] Kubernetes deployment configs

## 🤝 Contributing

Contributions welcome! This microservice architecture makes it easy to:

- Add new AI capabilities
- Swap LLM providers
- Extend code analysis tools
- Add new programming languages

## 📄 License

[Your License Here]

## 🔗 Links

- [LangChain Documentation](https://python.langchain.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ES256 JWT Specification](https://datatracker.ietf.org/doc/html/rfc7518)

---

**Note**: This platform uses modern ES256 JWT authentication and LangChain's latest (non-deprecated) API. Make sure to update your Supabase configuration and install all required dependencies in both the main project and the `code_assist` folder.
