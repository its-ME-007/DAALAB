from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from container_runner import ContainerRunner
from auth import auth_bp, get_user_id_from_request  # Import your authentication router
import uvicorn
import os
from supabase import create_client
from dotenv import load_dotenv

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
    algorithm_name: str = None
    input_size: int = None

class CodeResponse(BaseModel):
    output: str
    runtime: float
    success: bool
    error: str = None
    saved_to_db: bool = False

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

@app.post("/api/run-code", response_model=CodeResponse)
async def run_code(request: CodeRequest, auth_request: Request):
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

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Python Code Runner API"}

@app.get("/api/runtime-data")
async def get_runtime_data(auth_request: Request):
    """Get algorithm runtime data for the authenticated user"""
    try:
        user_id = get_user_id_from_request(auth_request)
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get runtime data from Supabase
        response = supabase.table('algorithm_runtimes')\
            .select('*')\
            .eq('user_id', user_id)\
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 