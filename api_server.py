"""API Server - Frontend Gateway for DAALAB Platform

ARCHITECTURE ROLE:
This service acts as a FRONTEND/API GATEWAY that:
1. Serves static HTML files (UI)
2. Handles user authentication (login/signup)
3. Manages code file storage in Supabase database
4. Forwards code execution requests to the scheduler-worker architecture via load balancer
5. Provides AI analysis and complexity analysis endpoints

EXECUTION FLOW:
Frontend (HTML) → api_server.py (port 8010) → Load Balancer (port 8080) 
→ Scheduler (port 8000) → Workers (ports 8001, 8002) → Docker containers

This service does NOT execute code directly anymore - all execution is delegated
to the distributed scheduler-worker system for better load distribution, fault tolerance,
and complexity-aware scheduling.

KEY ENDPOINTS:
- /api/run-code: Forward Python execution to scheduler
- /api/run-cpp: Forward C++ execution to scheduler
- /api/ai/*: AI-powered code analysis (direct to AI service)
- /api/code/*: Database operations for code files
- /api/auth/*: User authentication
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from auth import auth_bp, get_user_id_from_request
from code_assist import AIServiceClient, check_ai_service  # ✅ Already imported
import uvicorn
import os
from supabase import create_client
from dotenv import load_dotenv
from visualize import register_visualization_routes
import httpx
from complexity_analyzer import ComplexityAnalyzer

load_dotenv()

app = FastAPI(title="Python Code Runner API (Frontend Gateway)", version="2.0.0")

# Load balancer configuration
LOAD_BALANCER_URL = os.getenv("LOAD_BALANCER_URL", "http://localhost:8080")

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register authentication routes
app.include_router(auth_bp, prefix="/api/auth")

# ====================================================================
# REQUEST/RESPONSE MODELS
# ====================================================================

class CodeRequest(BaseModel):
    code: str
    algorithm_name: Optional[str] = None
    input_size: Optional[int] = None

class CodeResponse(BaseModel):
    output: str
    runtime: float
    success: bool
    error: Optional[str] = None
    saved_to_db: bool = False

class AIAnalysisRequest(BaseModel):
    code: str
    language: str = "python"
    query: Optional[str] = None
    session_id: Optional[str] = None

class AIAnalysisResponse(BaseModel):
    success: bool
    response: str
    analysis: Optional[Dict[str, Any]] = None
    suggestions: Optional[list] = None
    session_id: Optional[str] = None
    error: Optional[str] = None

class CodeFileUpsert(BaseModel):
    content: str

class CodeFileResponse(BaseModel):
    success: bool
    file: Optional[Dict[str, Any]] = None
    message: str

class ComplexityAnalysisRequest(BaseModel):
    code: str
    language: str = "python"

class ComplexityAnalysisResponse(BaseModel):
    success: bool
    time_complexity: Optional[str] = None
    time_complexity_class: Optional[str] = None
    space_complexity: Optional[str] = None
    space_complexity_class: Optional[str] = None
    explanation: Optional[str] = None
    best_case: Optional[str] = None
    average_case: Optional[str] = None
    worst_case: Optional[str] = None
    algorithm_name: Optional[str] = None
    error: Optional[str] = None

# ====================================================================
# HTML PAGE ROUTES
# ====================================================================

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.get("/index.html")
async def index_page():
    return FileResponse("static/index.html")

@app.get("/login.html")
async def login_page():
    return FileResponse("static/login.html")

@app.get("/signup.html")
async def signup_page():
    return FileResponse("static/signup.html")

@app.get("/visualization.html")
async def visualization_page():
    return FileResponse("static/visualization.html")

@app.get("/compiler.html")
async def compiler_page():
    return FileResponse("static/compiler.html")

@app.get("/cpp_compiler.html")
async def cpp_compiler_page():
    return FileResponse("static/cpp_compiler.html")

# ====================================================================
# CODE FILE MANAGEMENT
# ====================================================================

@app.post("/api/submit-code")
async def submit_code_to_ai(auth_request: Request):
    """Read user's code files from database and send to AI service."""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return {"success": False, "message": "Authentication required"}
        
        result = supabase.table('user_code_files')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            return {"success": False, "message": "No code files found"}
        
        # Get AI service URL from environment or use first worker URL as fallback
        ai_service_url = os.getenv("AI_SERVICE_URL")
        if not ai_service_url:
            worker_urls = os.getenv("WORKER_URLS", "http://localhost:8001")
            ai_service_url = worker_urls.split(",")[0].strip()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for file_record in result.data:
                upload_data = {
                    'filename': file_record['filename'],
                    'code': file_record['code_content']
                }
                response = await client.post(
                    f"{ai_service_url}/upload",
                    json=upload_data
                )
                if response.status_code != 200:
                    return {"success": False, "message": f"Failed to upload {file_record['filename']}"}
        
        return {"success": True, "message": "Code files submitted to AI service"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

@app.post("/api/code/{file_type}")
async def upsert_code_file(auth_request: Request, file_type: str, file_data: CodeFileUpsert):
    """Save or update user's code file (python or cpp)."""
    try:
        if file_type not in ['python', 'cpp']:
            return CodeFileResponse(success=False, message="Invalid file type")
        
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return CodeFileResponse(success=False, message="Authentication required")
        
        result = supabase.table('user_code_files').upsert(
            {
                'user_id': user_id,
                'file_type': file_type,
                'code_content': file_data.content
            },
            on_conflict='user_id,file_type'
        ).execute()
        
        if result.data:
            return CodeFileResponse(
                success=True,
                file=result.data[0],
                message=f"{file_type} file saved successfully"
            )
        else:
            return CodeFileResponse(success=False, message="Failed to save file")
    except Exception as e:
        return CodeFileResponse(success=False, message=f"Error: {str(e)}")

@app.get("/api/code/{file_type}")
async def get_code_file(auth_request: Request, file_type: str):
    """Get user's specific code file."""
    try:
        if file_type not in ['python', 'cpp']:
            return CodeFileResponse(success=False, message="Invalid file type")
        
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return CodeFileResponse(success=False, message="Authentication required")
        
        result = supabase.table('user_code_files')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('file_type', file_type)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return CodeFileResponse(
                success=True,
                file=result.data[0],
                message=f"{file_type} file retrieved"
            )
        else:
            return CodeFileResponse(success=False, message=f"No {file_type} file found")
    except Exception as e:
        return CodeFileResponse(success=False, message=f"Error: {str(e)}")
    
@app.get("/agent.html")
async def agent_page():
    """Serve the AI agent HTML page"""
    return FileResponse("static/agent.html")

@app.get("/api/code")
async def get_all_code_files(auth_request: Request):
    """Get all user's code files."""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return {"success": False, "message": "Authentication required", "files": []}
        
        result = supabase.table('user_code_files')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        return {
            "success": True,
            "files": result.data or [],
            "message": f"Retrieved {len(result.data or [])} file(s)"
        }
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}", "files": []}

# ====================================================================
# CODE EXECUTION ENDPOINTS
# ====================================================================

@app.post("/api/run-code", response_model=CodeResponse)
async def run_code(auth_request: Request, request: CodeRequest):
    """
    Execute Python code with complexity analysis.
    Flow: Save to DB → Analyze complexity (Mistral) → Forward to Load Balancer → Scheduler → Worker
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        user_id = get_user_id_from_request(auth_request)
        
        # Step 1: Save code to Supabase if user is authenticated
        if user_id:
            try:
                supabase.table('user_code_files').upsert({
                    'user_id': user_id,
                    'file_type': 'python',
                    'code_content': request.code
                }, on_conflict='user_id,file_type').execute()
            except Exception as db_error:
                print(f"Database save warning: {db_error}")
        
        # Step 2: Forward to load balancer -> scheduler -> worker (scheduler will analyze complexity)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LOAD_BALANCER_URL}/api/run-code",
                json={
                    "code": request.code,
                    "language": "python",
                    "user_id": user_id,
                    "algorithm_name": request.algorithm_name,
                    "input_size": request.input_size
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Scheduler error: {response.text}"
                )
            
            result = response.json()
            output = result.get("output", "")
            runtime = result.get("runtime", 0.0)
            success = result.get("success", False)
            error = result.get("error")
            runtime_ms = runtime * 1000
        
        # Step 4: Save runtime data to database if algorithm metadata provided
        saved_to_db = False
        if request.algorithm_name and request.input_size and user_id:
            try:
                supabase.table('algorithm_runtimes').insert({
                    'user_id': user_id,
                    'algorithm_name': request.algorithm_name,
                    'input_size': request.input_size,
                    'execution_time_ms': runtime_ms,
                    'code_snippet': request.code[:1000],
                    'output_result': output[:1000]
                }).execute()
                saved_to_db = True
            except Exception as db_error:
                print(f"Database save error: {db_error}")
        
        return CodeResponse(
            output=output,
            runtime=runtime,
            success=success,
            error=error,
            saved_to_db=saved_to_db
        )
        
    except httpx.TimeoutException:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error="Request timeout: Code execution took too long",
            saved_to_db=False
        )
    except Exception as e:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error=f"Server error: {str(e)}",
            saved_to_db=False
        )

@app.post("/api/run-cpp", response_model=CodeResponse)
async def run_cpp_code(auth_request: Request, request: CodeRequest):
    """
    Execute C++ code with complexity analysis.
    Flow: Save to DB → Analyze complexity (Mistral) → Forward to Load Balancer → Scheduler → Worker
    """
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        user_id = get_user_id_from_request(auth_request)
        
        # Step 1: Save code to Supabase if user is authenticated
        if user_id:
            try:
                supabase.table('user_code_files').upsert({
                    'user_id': user_id,
                    'file_type': 'cpp',
                    'code_content': request.code
                }, on_conflict='user_id,file_type').execute()
            except Exception as db_error:
                print(f"Database save warning: {db_error}")
        
        # Step 2: Forward to load balancer -> scheduler -> worker (scheduler will analyze complexity)
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{LOAD_BALANCER_URL}/api/run-code",
                json={
                    "code": request.code,
                    "language": "cpp",
                    "user_id": user_id,
                    "algorithm_name": request.algorithm_name,
                    "input_size": request.input_size
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Scheduler error: {response.text}"
                )
            
            result = response.json()
            output = result.get("output", "")
            runtime = result.get("runtime", 0.0)
            success = result.get("success", False)
            error = result.get("error")
            runtime_ms = runtime * 1000
        
        # Step 4: Save runtime data to database if algorithm metadata provided
        saved_to_db = False
        if request.algorithm_name and request.input_size and user_id:
            try:
                supabase.table('algorithm_runtimes').insert({
                    'user_id': user_id,
                    'algorithm_name': request.algorithm_name,
                    'input_size': request.input_size,
                    'execution_time_ms': runtime_ms,
                    'code_snippet': request.code[:1000],
                    'output_result': output[:1000]
                }).execute()
                saved_to_db = True
            except Exception as db_error:
                print(f"Database save error: {db_error}")
        
        return CodeResponse(
            output=output,
            runtime=runtime,
            success=success,
            error=error,
            saved_to_db=saved_to_db
        )
        
    except httpx.TimeoutException:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error="Request timeout: Code execution took too long",
            saved_to_db=False
        )
    except Exception as e:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error=f"Server error: {str(e)}",
            saved_to_db=False
        )

# ====================================================================
# AI CODE ANALYSIS ENDPOINTS
# ====================================================================

@app.post("/api/ai/analyze", response_model=AIAnalysisResponse)
async def analyze_code_with_ai(auth_request: Request, request: AIAnalysisRequest):
    """Analyze code using AI microservice."""
    try:
        user_id = get_user_id_from_request(auth_request)
        ai_client = AIServiceClient()
        
        result = await ai_client.analyze_code(
            code=request.code,
            language=request.language,
            query=request.query,
            session_id=request.session_id or user_id
        )
        
        return AIAnalysisResponse(**result)
        
    except Exception as e:
        return AIAnalysisResponse(
            success=False,
            response="",
            error=f"AI service error: {str(e)}"
        )

@app.post("/api/ai/chat")
async def chat_with_ai(auth_request: Request, request: AIAnalysisRequest):
    """Interactive chat with AI about code."""
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query is required for chat")
        
        user_id = get_user_id_from_request(auth_request)
        ai_client = AIServiceClient()
        
        result = await ai_client.chat(
            code=request.code,
            query=request.query,
            language=request.language,
            session_id=request.session_id or user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "success": False,
            "response": "",
            "error": f"AI service error: {str(e)}"
        }

@app.get("/api/ai/health")
async def check_ai_service_health():
    """Check if AI microservice is available."""
    try:
        ai_client = AIServiceClient()
        health = await ai_client.health_check()
        return {"ai_service_available": True, "details": health}
    except Exception as e:
        return {"ai_service_available": False, "error": str(e)}

@app.delete("/api/ai/session/{session_id}")
async def clear_ai_session(auth_request: Request, session_id: str):
    """Clear AI conversation history for a session."""
    try:
        ai_client = AIServiceClient()
        result = await ai_client.clear_session(session_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====================================================================
# HEALTH CHECK & RUNTIME DATA
# ====================================================================

@app.get("/api/health")
async def health_check():
    """Health check endpoint with AI service status"""
    ai_service_healthy = await check_ai_service()
    return {
        "status": "healthy",
        "service": "Python Code Runner API",
        "ai_service": "healthy" if ai_service_healthy else "unavailable"
    }

@app.get("/api/runtime-summary")
async def get_runtime_summary(auth_request: Request):
    """Get algorithm performance summary for the authenticated user"""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        response = supabase.rpc('get_algorithm_performance_summary', {
            'user_id_param': user_id
        }).execute()
        
        return {
            'success': True,
            'data': response.data
        }
        
    except Exception as e:
        try:
            response = supabase.table('algorithm_runtimes')\
                .select('algorithm_name, input_size, execution_time_ms')\
                .eq('user_id', user_id)\
                .execute()
            
            summary = {}
            for record in response.data:
                key = f"{record['algorithm_name']}_{record['input_size']}"
                if key not in summary:
                    summary[key] = {
                        'algorithm_name': record['algorithm_name'],
                        'input_size': record['input_size'],
                        'execution_count': 0,
                        'avg_execution_time_ms': 0,
                        'times': []
                    }
                summary[key]['execution_count'] += 1
                summary[key]['times'].append(record['execution_time_ms'])
            
            for key in summary:
                times = summary[key]['times']
                summary[key]['avg_execution_time_ms'] = sum(times) / len(times)
                summary[key]['min_execution_time_ms'] = min(times)
                summary[key]['max_execution_time_ms'] = max(times)
                del summary[key]['times']
            
            return {
                'success': True,
                'data': list(summary.values())
            }
            
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve runtime summary: {str(e)}")

# ====================================================================
# COMPLEXITY ANALYSIS
# ====================================================================

@app.post("/api/analyze-complexity", response_model=ComplexityAnalysisResponse)
async def analyze_complexity(request: ComplexityAnalysisRequest):
    """Analyze code complexity using Mistral AI"""
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        analyzer = ComplexityAnalyzer()
        result = analyzer.analyze_code(request.code, request.language)
        
        return ComplexityAnalysisResponse(
            success=True,
            time_complexity=result.get("time_complexity"),
            time_complexity_class=result.get("time_complexity_class"),
            space_complexity=result.get("space_complexity"),
            space_complexity_class=result.get("space_complexity_class"),
            explanation=result.get("explanation"),
            best_case=result.get("best_case"),
            average_case=result.get("average_case"),
            worst_case=result.get("worst_case"),
            algorithm_name=result.get("algorithm_name")
        )
        
    except Exception as e:
        print(f"Complexity analysis error: {e}")
        return ComplexityAnalysisResponse(
            success=False,
            error=f"Analysis failed: {str(e)}"
        )

# Register visualization routes
register_visualization_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)