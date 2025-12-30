from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from container_runner import ContainerRunner, CppContainerRunner
from auth import auth_bp, get_user_id_from_request  # Import your authentication router
from code_assist import AIServiceClient, check_ai_service  # Import AI service client
import uvicorn
import os
from supabase import create_client
from dotenv import load_dotenv
from visualize import register_visualization_routes
import httpx

load_dotenv()

app = FastAPI(title="Python Code Runner API", version="1.0.0")

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register authentication routes
app.include_router(auth_bp, prefix="/api/auth")

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

@app.post("/api/submit-code")
async def submit_code_to_ai(auth_request: Request):
    """Read user's code files from database and send to AI service."""
    try:
        # Get authenticated user
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return {"success": False, "message": "Authentication required"}
        
        # Get user's files from database
        result = supabase.table('user_code_files')\
            .select('*')\
            .eq('user_id', user_id)\
            .execute()
        
        if not result.data:
            return {"success": False, "message": "No code files found"}
        
        # Upload each file to AI service using the new endpoint format
        async with httpx.AsyncClient(timeout=30.0) as client:
            for file_record in result.data:
                upload_data = {
                    'filename': file_record['filename'],
                    'code': file_record['code_content']
                }
                response = await client.post(
                    "http://localhost:8001/upload",
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
        # Validate file type
        if file_type not in ['python', 'cpp']:
            return CodeFileResponse(success=False, message="Invalid file type. Use 'python' or 'cpp'")
        
        # Get authenticated user
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return CodeFileResponse(success=False, message="Authentication required")
        
        # Upsert to database with conflict resolution on (user_id, file_type)
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
        # Validate file type
        if file_type not in ['python', 'cpp']:
            return CodeFileResponse(success=False, message="Invalid file type. Use 'python' or 'cpp'")
        
        # Get authenticated user
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return CodeFileResponse(success=False, message="Authentication required")
        
        # Get file from database
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

@app.get("/api/code")
async def get_all_code_files(auth_request: Request):
    """Get all user's code files."""
    try:
        # Get authenticated user
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            return {"success": False, "message": "Authentication required", "files": []}
        
        # Get all files from database
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

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/index.html")
async def index_page():
    """Serve the main HTML page (alternative route)"""
    return FileResponse("static/index.html")

@app.get("/login.html")
async def login_page():
    """Serve the login HTML page"""
    return FileResponse("static/login.html")

@app.get("/signup.html")
async def signup_page():
    """Serve the signup HTML page"""
    return FileResponse("static/signup.html")

@app.get("/visualization.html")
async def visualization_page():
    """Serve the visualization HTML page"""
    return FileResponse("static/visualization.html")

@app.get("/compiler.html")
async def compiler_page():
    """Serve the compiler HTML page"""
    return FileResponse("static/compiler.html")

@app.get("/cpp_compiler.html")
async def cpp_compiler_page():
    """Serve the C++ compiler HTML page"""
    return FileResponse("static/cpp_compiler.html")

@app.post("/api/run-code", response_model=CodeResponse)
async def run_code(auth_request: Request, request: CodeRequest):
    """Execute Python code in a container and save runtime data"""
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        runner = ContainerRunner()
        output, runtime = runner.run_code(request.code)
        
        # Convert runtime to milliseconds for database storage
        runtime_ms = runtime * 1000
        
        # Try to save to database if algorithm details are provided
        saved_to_db = False
        if request.algorithm_name and request.input_size:
            try:
                # Get user ID from authentication
                user_id = get_user_id_from_request(auth_request)
                
                if user_id:
                    # Save to Supabase
                    supabase.table('algorithm_runtimes').insert({
                        'user_id': user_id,
                        'algorithm_name': request.algorithm_name,
                        'input_size': request.input_size,
                        'execution_time_ms': runtime_ms,
                        'code_snippet': request.code[:1000],  # Limit code snippet length
                        'output_result': output[:1000]  # Limit output length
                    }).execute()
                    saved_to_db = True
                    print(f"Saved runtime data: {request.algorithm_name}, size: {request.input_size}, time: {runtime_ms}ms")
                else:
                    print("No user ID found, skipping database save")
            except Exception as db_error:
                print(f"Database save error: {db_error}")
                # Don't fail the request if database save fails
        
        if output.startswith("Error:"):
            return CodeResponse(
                output="",
                runtime=runtime,
                success=False,
                error=output,
                saved_to_db=saved_to_db
            )
        
        return CodeResponse(
            output=output,
            runtime=runtime,
            success=True,
            saved_to_db=saved_to_db
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
    """Execute C++ code in a container and save runtime data"""
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        runner = CppContainerRunner()
        output, runtime = runner.run_code(request.code)
        
        # Convert runtime to milliseconds for database storage
        runtime_ms = runtime * 1000
        
        # Try to save to database if algorithm details are provided
        saved_to_db = False
        if request.algorithm_name and request.input_size:
            try:
                # Get user ID from authentication
                user_id = get_user_id_from_request(auth_request)
                
                if user_id:
                    # Save to Supabase
                    supabase.table('algorithm_runtimes').insert({
                        'user_id': user_id,
                        'algorithm_name': request.algorithm_name,
                        'input_size': request.input_size,
                        'execution_time_ms': runtime_ms,
                        'code_snippet': request.code[:1000],  # Limit code snippet length
                        'output_result': output[:1000]  # Limit output length
                    }).execute()
                    saved_to_db = True
                    print(f"Saved C++ runtime data: {request.algorithm_name}, size: {request.input_size}, time: {runtime_ms}ms")
                else:
                    print("No user ID found, skipping database save")
            except Exception as db_error:
                print(f"Database save error: {db_error}")
                # Don't fail the request if database save fails
        
        if output.startswith("Error:"):
            return CodeResponse(
                output="",
                runtime=runtime,
                success=False,
                error=output,
                saved_to_db=saved_to_db
            )
        
        return CodeResponse(
            output=output,
            runtime=runtime,
            success=True,
            saved_to_db=saved_to_db
        )
        
    except Exception as e:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error=f"Server error: {str(e)}",
            saved_to_db=False
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    ai_service_healthy = await check_ai_service()
    return {
        "status": "healthy",
        "service": "Python Code Runner API",
        "ai_service": "healthy" if ai_service_healthy else "unavailable"
    }

# ====================================================================
# 🤖  AI CODE ANALYSIS ENDPOINTS (Microservice Integration)
# ====================================================================

@app.post("/api/ai/analyze", response_model=AIAnalysisResponse)
async def analyze_code_with_ai(auth_request: Request, request: AIAnalysisRequest):
    """
    Analyze code using AI microservice.
    
    This endpoint forwards the code to the AI helper microservice which uses
    LangChain agents to provide intelligent code analysis, suggestions, and insights.
    """
    try:
        # Optional: Check authentication if required
        user_id = get_user_id_from_request(auth_request)
        
        # Initialize AI service client
        ai_client = AIServiceClient()
        
        # Send request to AI microservice
        result = await ai_client.analyze_code(
            code=request.code,
            language=request.language,
            query=request.query,
            session_id=request.session_id or user_id  # Use user_id as session if available
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
    """
    Interactive chat with AI about code.
    
    Allows users to ask specific questions about their code and get
    conversational responses from the AI agent.
    """
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
# 📊  RUNTIME DATA ENDPOINTS
# ====================================================================
        
    except Exception as e:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error=f"Server error: {str(e)}",
            saved_to_db=False
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Python Code Runner API"}

@app.get("/api/runtime-data")
async def get_runtime_data(auth_request: Request):
    """Get all algorithm runtime data from the database"""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get ALL runtime data from Supabase (not just user-specific)
        response = supabase.table('algorithm_runtimes')\
            .select('*')\
            .order('created_at', desc=True)\
            .execute()
        
        return {
            'success': True,
            'data': response.data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve runtime data: {str(e)}")

@app.get("/api/runtime-summary")
async def get_runtime_summary(auth_request: Request):
    """Get algorithm performance summary for the authenticated user"""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get performance summary from the view
        response = supabase.rpc('get_algorithm_performance_summary', {
            'user_id_param': user_id
        }).execute()
        
        return {
            'success': True,
            'data': response.data
        }
        
    except Exception as e:
        # Fallback to direct query if RPC doesn't exist
        try:
            response = supabase.table('algorithm_runtimes')\
                .select('algorithm_name, input_size, execution_time_ms')\
                .eq('user_id', user_id)\
                .execute()
            
            # Process data to create summary
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
            
            # Calculate averages
            for key in summary:
                times = summary[key]['times']
                summary[key]['avg_execution_time_ms'] = sum(times) / len(times)
                summary[key]['min_execution_time_ms'] = min(times)
                summary[key]['max_execution_time_ms'] = max(times)
                del summary[key]['times']  # Remove raw times from response
            
            return {
                'success': True,
                'data': list(summary.values())
            }
            
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve runtime summary: {str(e)}")

register_visualization_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010) 