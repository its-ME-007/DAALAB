from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from container_runner import ContainerRunner
from auth import auth_bp  # Import your authentication router
import uvicorn
import os

app = FastAPI(title="Python Code Runner API", version="1.0.0")

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

class CodeResponse(BaseModel):
    output: str
    runtime: float
    success: bool
    error: str = None

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
async def run_code(request: CodeRequest):
    """Execute Python code in a container"""
    try:
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        runner = ContainerRunner()
        output, runtime = runner.run_code(request.code)
        
        if output.startswith("Error:"):
            return CodeResponse(
                output="",
                runtime=runtime,
                success=False,
                error=output
            )
        
        return CodeResponse(
            output=output,
            runtime=runtime,
            success=True
        )
        
    except Exception as e:
        return CodeResponse(
            output="",
            runtime=0.0,
            success=False,
            error=f"Server error: {str(e)}"
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Python Code Runner API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 