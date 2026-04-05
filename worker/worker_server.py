"""Worker execution service for Docker-based code execution.

This service:
1. Receives execution requests from scheduler
2. Manages job queue and worker state
3. Executes code in isolated Docker containers
4. Reports results back to scheduler/database
"""

import os
import uuid
import tempfile
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime, timezone
from typing import Dict
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import asyncio

from worker.container_runner import ContainerRunner, CppContainerRunner
from worker.worker_state import WorkerState
from common.models import (
    ExecutionRequest,
    ExecutionResult,
    WorkerState as WorkerStateModel,
    HealthResponse,
    Language
)

load_dotenv()

# ============================================================================
# Worker State Management
# ============================================================================

WORKER_ID = os.getenv("WORKER_ID", f"worker-{uuid.uuid4().hex[:8]}")
ENABLE_RESOURCE_MONITORING = os.getenv("ENABLE_RESOURCE_MONITORING", "true").lower() == "true"

# Initialize worker state
worker_state = WorkerState(
    worker_id=WORKER_ID,
    enable_resource_monitoring=ENABLE_RESOURCE_MONITORING
)

# Container runners
python_runner = ContainerRunner()
cpp_runner = CppContainerRunner()

# Job execution lock (prevent concurrent executions)
execution_lock = asyncio.Lock()

# Job results storage (in-memory, should be replaced with DB/Redis in production)
job_results: Dict[str, ExecutionResult] = {}

print(f"[WORKER] Worker initialized: {WORKER_ID}")
print(f"[MONITOR] Resource monitoring: {'enabled' if ENABLE_RESOURCE_MONITORING else 'disabled'}")


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with async context manager."""
    # Startup
    print(f"[STARTUP] Worker {WORKER_ID} starting up...")
    worker_state.mark_healthy()
    worker_state.update_heartbeat()
    
    yield
    
    # Shutdown
    print(f"[SHUTDOWN] Worker {WORKER_ID} shutting down...")
    worker_state.mark_unhealthy()


app = FastAPI(
    title="DAALAB Worker Service",
    description="Isolated code execution worker with Docker containers",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Execution Logic
# ============================================================================

async def execute_job(request: ExecutionRequest):
    """
    Execute a job with locking to prevent concurrent executions.
    
    This function runs asynchronously and ensures only one job executes at a time.
    """
    job_id = request.job_id
    estimated_cost_ms = request.estimated_cost_ms
    
    # Acquire lock to prevent concurrent executions
    async with execution_lock:
        try:
            print(f"[EXEC] Executing job {job_id} ({request.language.value})")
            
            # Start execution
            start_time = time.time()
            
            # Select appropriate runner
            if request.language == Language.PYTHON:
                output, runtime = python_runner.run_code(request.code)
            elif request.language == Language.CPP:
                output, runtime = cpp_runner.run_code(request.code)
            else:
                raise ValueError(f"Unsupported language: {request.language}")
            
            actual_runtime_ms = runtime * 1000  # Convert to ms
            
            # Check if execution succeeded
            success = not output.startswith("Error:")
            error = output if not success else None
            
            # Create result
            result = ExecutionResult(
                job_id=job_id,
                success=success,
                output=output if success else "",
                error=error,
                actual_runtime_ms=actual_runtime_ms,
                exit_code=0 if success else 1,
                worker_id=WORKER_ID,
                completed_at=datetime.now(timezone.utc)
            )
            
            # Store result
            job_results[job_id] = result
            
            print(f"[SUCCESS] Job {job_id} completed in {actual_runtime_ms:.2f}ms")
            
        except Exception as e:
            print(f"[ERROR] Job {job_id} failed: {e}")
            
            # Store error result
            result = ExecutionResult(
                job_id=job_id,
                success=False,
                output="",
                error=str(e),
                actual_runtime_ms=0.0,
                exit_code=1,
                worker_id=WORKER_ID,
                completed_at=datetime.now(timezone.utc)
            )
            job_results[job_id] = result
        
        finally:
            # Decrement queue cost (this also decrements active jobs)
            worker_state.decrement_queue_cost(estimated_cost_ms)
            worker_state.update_heartbeat()


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/execute")
async def execute_code(
    request: ExecutionRequest,
    background_tasks: BackgroundTasks
):
    """
    Execute code in Docker container.
    
    This endpoint:
    1. Accepts job from scheduler
    2. Increments queue cost immediately
    3. Executes job in background
    4. Returns job_id for status polling
    """
    try:
        # Increment queue cost immediately
        worker_state.increment_queue_cost(request.estimated_cost_ms)
        
        print(f"[QUEUE] Received job {request.job_id} (estimated: {request.estimated_cost_ms}ms)")
        
        # Schedule background execution
        background_tasks.add_task(execute_job, request)
        
        return {
            "job_id": request.job_id,
            "status": "queued",
            "worker_id": WORKER_ID,
            "message": "Job accepted and queued for execution"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """
    Get current worker state.
    
    Called by scheduler to make routing decisions.
    """
    state = worker_state.get_state()
    return state.model_dump()


@app.get("/job/{job_id}")
async def get_job_result(job_id: str):
    """
    Get execution result for a specific job.
    
    Args:
        job_id: Job identifier
    
    Returns:
        ExecutionResult if job is complete, or status if still running
    """
    if job_id in job_results:
        return job_results[job_id].model_dump()
    
    # Job not found in results - might still be running
    current_state = worker_state.get_state()
    
    if current_state.active_jobs > 0:
        return {
            "job_id": job_id,
            "status": "running",
            "message": "Job is currently executing"
        }
    
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for load balancers and orchestrators.
    """
    state = worker_state.get_state()
    
    return HealthResponse(
        status="healthy" if state.is_healthy else "unhealthy",
        service=f"Worker ({WORKER_ID})",
        timestamp=datetime.now(timezone.utc),
        details={
            "worker_id": WORKER_ID,
            "queue_cost_ms": state.queue_cost_ms,
            "active_jobs": state.active_jobs,
            "cpu_util": state.cpu_util,
            "mem_util": state.mem_util
        }
    )


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("WORKER_PORT", 8001))
    host = os.getenv("WORKER_HOST", "0.0.0.0")
    
    print(f"[START] Starting worker on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
