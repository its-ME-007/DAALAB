# AI Code Helper Microservice Architecture

## 🏗️ Architecture Overview

The application is now split into **two independent microservices**:

### 1. Main API Service (Port 8000)
- Code execution (Python & C++)
- Authentication & JWT verification
- Database operations (Supabase)
- Algorithm runtime tracking
- Data visualization
- **HTTP client** to communicate with AI service

### 2. AI Helper Service (Port 8001)
- LangChain-powered code analysis
- AI agent with specialized tools
- Code structure analysis
- Bug detection & suggestions
- Complexity metrics
- **Independent deployment**

## 📋 Prerequisites

1. **Python 3.9+**
2. **Docker** (for code execution containers)
3. **Supabase Account** with configured project
4. **Groq API Key** (for fast AI inference with LLMs)

## 🔧 Setup Instructions

### Step 1: Install Dependencies

```powershell
# Install all required packages
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Edit the `.env` file with your credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://rnpllovzmcfgjsfrkgxj.supabase.co
SUPABASE_KEY=your-actual-anon-key-here

# JWT Configuration
SUPABASE_JWKS_URL=https://rnpllovzmcfgjsfrkgxj.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_KID=c2d594d8-319a-4d63-9b06-7719e03e9f5a

# Groq for AI Service (fast LLM inference)
GROQ_API_KEY=your-groq-api-key-here

# Service Configuration
PORT=8000
AI_SERVICE_PORT=8001
AI_SERVICE_URL=http://localhost:8001
```

### Step 3: Initialize Database

Run the SQL schema to set up your database:

```powershell
# Apply schema.sql to your Supabase database
# Go to Supabase Dashboard -> SQL Editor -> New Query
# Copy and paste the contents of schema.sql
```

## 🚀 Running the Services

### Option 1: Run Both Services Separately (Recommended)

**Terminal 1 - Main API Service:**
```powershell
python api_server.py
```

**Terminal 2 - AI Helper Service:**
```powershell
python -m helper_agent.agent_service
```

### Option 2: Run Both Services (PowerShell Script)

Create a file `start_services.ps1`:

```powershell
# Start both microservices
$mainService = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python api_server.py" -PassThru
$aiService = Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m helper_agent.agent_service" -PassThru

Write-Host "Services started!"
Write-Host "Main API: http://localhost:8000"
Write-Host "AI Service: http://localhost:8001"
Write-Host ""
Write-Host "Press any key to stop services..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Stop services
Stop-Process -Id $mainService.Id
Stop-Process -Id $aiService.Id
```

Run it:
```powershell
./start_services.ps1
```

## 🔍 API Endpoints

### Main Service (http://localhost:8000)

#### Code Execution
- `POST /api/run-code` - Execute Python code
- `POST /api/run-cpp` - Execute C++ code

#### Authentication
- `POST /api/auth/signup` - Create new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

#### AI Integration
- `POST /api/ai/analyze` - Analyze code with AI
  ```json
  {
    "code": "def hello():\n    print('world')",
    "language": "python",
    "query": "What does this code do?"
  }
  ```

- `POST /api/ai/chat` - Chat with AI about code
  ```json
  {
    "code": "your code here",
    "query": "How can I optimize this?",
    "session_id": "optional-session-id"
  }
  ```

- `GET /api/ai/health` - Check AI service status
- `DELETE /api/ai/session/{session_id}` - Clear conversation history

#### Data & Visualization
- `GET /api/runtime-data` - Get algorithm runtime data
- `GET /api/runtime-summary` - Get performance summary
- `GET /api/health` - Health check

### AI Service (http://localhost:8001)

- `POST /analyze` - Direct code analysis
- `POST /chat` - Interactive AI chat
- `GET /health` - Service health check
- `DELETE /session/{session_id}` - Clear session

## 🧪 Testing the AI Service

### Test with curl:

```powershell
# Analyze code
curl -X POST http://localhost:8001/analyze `
  -H "Content-Type: application/json" `
  -d '{
    "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
    "language": "python"
  }'
```

### Test with Python:

```python
import asyncio
from helper_agent import analyze_code

async def test():
    code = """
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    """
    
    result = await analyze_code(
        code=code,
        query="How can I optimize this sorting algorithm?"
    )
    
    print(result['response'])

asyncio.run(test())
```

## 🔐 Security Features

1. **ES256 JWT Verification** - Modern elliptic curve cryptography
2. **JWKS Key Rotation** - Automatic public key updates
3. **Row Level Security** - User-specific data isolation
4. **Signature Verification** - All tokens validated against Supabase

## 📊 LangChain Tools

The AI agent includes specialized tools:

1. **analyze_code_structure** - Extract functions, classes, imports
2. **detect_code_issues** - Find bugs, security issues, anti-patterns
3. **suggest_improvements** - Optimization recommendations
4. **calculate_complexity** - Cyclomatic complexity metrics

## 🌐 Deployment

### Production Considerations:

1. **Separate Hosting**:
   - Main API: Deploy to Heroku/Railway/Render
   - AI Service: Deploy to separate instance (can be same provider)
   - Update `AI_SERVICE_URL` to production URL

2. **Environment Variables**:
   - Use platform-specific secret management
   - Never commit real API keys

3. **CORS Configuration**:
   - Update `allow_origins` to specific domains
   - Remove wildcard (*) in production

4. **Scaling**:
   - AI service can scale independently
   - Use Redis for session storage (replace in-memory dict)
   - Consider rate limiting for AI endpoints

## 🐛 Troubleshooting

### AI Service Not Connecting
```powershell
# Check if AI service is running
curl http://localhost:8001/health

# Check environment variable
echo $env:AI_SERVICE_URL
```

### OpenAI API Errors
- Verify API key in `.env`
- Check OpenAI account credits
- Review rate limits

### JWT Verification Failures
- Ensure JWKS URL is correct
- Check Supabase project settings
- Verify token is not expired

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [Supabase Auth Docs](https://supabase.com/docs/guides/auth)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [ES256 JWT Standard](https://datatracker.ietf.org/doc/html/rfc7518)

## 🤝 Contributing

This microservice architecture allows for:
- Independent development of AI features
- Easy swapping of LLM providers
- Scalable deployment
- Clear separation of concerns
