"""Scheduler API Server - Main entry point for job submissions.

This service:
1. Receives code execution requests from clients
2. Analyzes code complexity using AI service
3. Estimates execution cost
4. Selects optimal worker using scheduling algorithm
5. Dispatches job to selected worker
6. Tracks job status and results
"""

import os
import uuid
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime, timezone
from typing import Dict, Optional
from dotenv import load_dotenv

from scheduler.scheduler import Scheduler
from scheduler.worker_registry import get_worker_registry
from scheduler.cost_model import estimate_execution_cost
from common.models import (
    JobRequest,
    JobResponse,
    JobStatusResponse,
    JobStatus,
    ExecutionRequest,
    ComplexityAnalysis,
    SchedulingMode,
    CodeResponse,
    HealthResponse,
    Language
)
from auth import get_user_id_from_request

load_dotenv()

app = FastAPI(
    title="DAALAB Scheduler Service",
    description="Complexity-aware job scheduler for distributed code execution",
    version="2.0.0"
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
# Configuration
# ============================================================================

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:5000")
SCHEDULING_MODE = SchedulingMode(os.getenv("SCHEDULING_MODE", "queue_cost"))

# Initialize scheduler
scheduler = Scheduler(mode=SCHEDULING_MODE)

# Initialize worker registry
worker_registry = get_worker_registry()

# Job tracking (in-memory, should be Redis/DB in production)
job_metadata: Dict[str, dict] = {}

# Job assignment map: tracks which jobs are assigned to which workers
# Format: {job_id: {worker_id, estimated_cost_ms, assigned_at}}
job_assignments: Dict[str, dict] = {}

# Worker load map: tracks current estimated load per worker
# Format: {worker_id: total_estimated_cost_ms}
worker_load_map: Dict[str, float] = {}

print(f"[SCHEDULER] Scheduler initialized with mode: {SCHEDULING_MODE.value}")
print(f"[AI] AI service: {AI_SERVICE_URL}")
print(f"[WORKERS] Worker registry: {worker_registry}")
print(f"[TRACKING] Job assignment tracking enabled")


# ============================================================================
# AI Service Integration
# ============================================================================

async def analyze_code_complexity(code: str, language: str) -> Optional[ComplexityAnalysis]:
    """
    Call AI service to analyze code complexity.
    
    Args:
        code: Source code to analyze
        language: Programming language
    
    Returns:
        ComplexityAnalysis or None if analysis fails
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/analyze_complexity",
                json={"code": code, "language": language}
            )
            
            if response.status_code == 200:
                data = response.json()
                return ComplexityAnalysis(
                    time_complexity=data.get("time_complexity", "UNKNOWN"),
                    space_complexity=data.get("space_complexity"),
                    confidence=data.get("confidence", 0.0),
                    explanation=data.get("explanation"),
                    algorithm_detected=data.get("algorithm_name")
                )
    
    except Exception as e:
        print(f"[WARNING] AI service unavailable: {e}")
    
    return None


# ============================================================================
# Job Submission Workflow
# ============================================================================

async def handle_job_request(job: JobRequest) -> JobResponse:
    """
    Main job submission handler implementing the scheduling algorithm.
    
    Steps:
    1. Analyze code complexity (AI service)
    2. Estimate execution cost
    3. Fetch worker states
    4. Select worker using scheduling algorithm
    5. Dispatch job to worker
    6. Return job_id and metadata
    """
    job_id = str(uuid.uuid4())
    
    # Step 1: Analyze complexity via AI service
    print(f"[ANALYSIS] Analyzing complexity for job {job_id}")
    complexity_analysis = await analyze_code_complexity(job.code, job.language.value)
    
    # Step 2: Estimate cost
    estimated_cost_ms = estimate_execution_cost(
        complexity_analysis,
        job.language,
        job.input_size or 1000
    )
    
    print(f"[COST] Estimated cost: {estimated_cost_ms:.2f}ms")
    
    # Step 3: Fetch worker states
    workers = await worker_registry.fetch_all_worker_states(use_cache=True)
    
    if not workers:
        raise HTTPException(status_code=503, detail="No workers available")
    
    # Update worker load map with in-flight jobs
    # This prevents race conditions when multiple jobs arrive simultaneously
    for worker in workers:
        if worker.worker_id not in worker_load_map:
            worker_load_map[worker.worker_id] = 0.0
    
    # Step 4: Select worker using scheduler-tracked load map
    result = scheduler.select_worker(workers, estimated_cost_ms, worker_load_map)
    
    if not result:
        raise HTTPException(status_code=503, detail="Worker selection failed")
    
    selected_worker, decision = result
    
    # Record job assignment in tracking map
    job_assignments[job_id] = {
        "worker_id": selected_worker.worker_id,
        "estimated_cost_ms": estimated_cost_ms,
        "assigned_at": datetime.now(timezone.utc)
    }
    
    # Update worker load map (increment)
    worker_load_map[selected_worker.worker_id] = worker_load_map.get(selected_worker.worker_id, 0.0) + estimated_cost_ms
    
    print(f"[WORKER] Selected worker: {selected_worker.worker_id}")
    print(f"[LOAD] Worker {selected_worker.worker_id} load: {worker_load_map[selected_worker.worker_id]:.0f}ms")
    print(f"[INFO] {decision.reasoning}")
    
    # Step 5: Dispatch job
    execution_request = ExecutionRequest(
        job_id=job_id,
        code=job.code,
        language=job.language,
        estimated_cost_ms=estimated_cost_ms,
        user_id=job.user_id,
        algorithm_name=job.algorithm_name,
        input_size=job.input_size
    )
    
    # Get worker URL using simple mapping
    worker_url = get_worker_url(selected_worker.worker_id)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{worker_url}/execute",
                json=execution_request.model_dump()
            )
            response.raise_for_status()
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to dispatch job to worker: {str(e)}"
        )
    
    # Store job metadata
    job_metadata[job_id] = {
        "job_id": job_id,
        "status": JobStatus.QUEUED,
        "submitted_at": datetime.now(timezone.utc),
        "complexity_analysis": complexity_analysis.model_dump() if complexity_analysis else None,
        "estimated_cost_ms": estimated_cost_ms,
        "selected_worker_id": selected_worker.worker_id,
        "scheduling_decision": decision.model_dump()
    }
    
    # Note: Job cleanup happens when client queries job status and finds it completed
    # See cleanup_completed_job() function below
    
    # Return response
    return JobResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        message="Job submitted successfully",
        estimated_wait_time_ms=selected_worker.queue_cost_ms,
        selected_worker_id=selected_worker.worker_id
    )


# ============================================================================
# Helper Functions
# ============================================================================

def get_worker_url(worker_id: str) -> str:
    """Get worker URL from worker ID using registry lookup.
    
    Args:
        worker_id: Worker identifier (e.g., "worker-1", "worker-2")
    
    Returns:
        Worker URL (e.g., "http://localhost:8001")
    
    Raises:
        ValueError: If worker_id not found in registry
    """
    url = worker_registry.get_worker_url_by_id(worker_id)
    if url is None:
        raise ValueError(f"Worker {worker_id} not found in registry")
    return url


# ============================================================================
# Job Cleanup Helpers
# ============================================================================

def cleanup_completed_job(job_id: str):
    """
    Clean up job from assignment map and update worker load map.
    
    Called when a job is found to be completed.
    """
    if job_id in job_assignments:
        assignment = job_assignments[job_id]
        worker_id = assignment["worker_id"]
        estimated_cost_ms = assignment["estimated_cost_ms"]
        
        # Decrement worker load
        if worker_id in worker_load_map:
            worker_load_map[worker_id] = max(0, worker_load_map[worker_id] - estimated_cost_ms)
            print(f"[CLEANUP] Job {job_id} completed, worker {worker_id} load: {worker_load_map[worker_id]:.0f}ms")
        
        # Remove from assignment map
        del job_assignments[job_id]


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/submit-job", response_model=JobResponse)
async def submit_job(auth_request: Request, job: JobRequest):
    """
    Submit a job for execution (async API).
    
    Returns job_id immediately. Client polls /api/job/{job_id} for results.
    """
    # Extract user ID from JWT
    user_id = get_user_id_from_request(auth_request)
    job.user_id = user_id
    
    return await handle_job_request(job)


@app.post("/api/run-code", response_model=CodeResponse)
async def run_code_sync(auth_request: Request, job: JobRequest):
    """
    Submit job and wait for completion (synchronous API for backward compatibility).
    
    This endpoint blocks until execution completes.
    """
    user_id = get_user_id_from_request(auth_request)
    job.user_id = user_id
    
    # Submit job
    job_response = await handle_job_request(job)
    job_id = job_response.job_id
    
    # Poll for result (with timeout)
    import asyncio
    max_wait_seconds = 60
    poll_interval = 0.5
    elapsed = 0
    
    while elapsed < max_wait_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        
        # Get result from worker
        metadata = job_metadata.get(job_id)
        if metadata:
            worker_url = get_worker_url(metadata["selected_worker_id"])
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{worker_url}/job/{job_id}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get("status") != "running":
                            # Job complete - cleanup assignment
                            cleanup_completed_job(job_id)
                            
                            # Return result
                            return CodeResponse(
                                output=result.get("output", ""),
                                runtime=result.get("actual_runtime_ms", 0) / 1000.0,
                                success=result.get("success", False),
                                error=result.get("error"),
                                saved_to_db=False,  # TODO: Implement DB save
                                job_id=job_id
                            )
            except:
                pass
    
    # Timeout
    raise HTTPException(status_code=408, detail="Job execution timeout")


@app.get("/api/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status and result of a submitted job.
    """
    if job_id not in job_metadata:
        raise HTTPException(status_code=404, detail="Job not found")
    
    metadata = job_metadata[job_id]
    
    # Try to get result from worker
    worker_url = get_worker_url(metadata["selected_worker_id"])
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{worker_url}/job/{job_id}")
            
            if response.status_code == 200:
                result_data = response.json()
                
                from common.models import ExecutionResult
                result = ExecutionResult(**result_data)
                
                # Cleanup completed job from assignment map
                cleanup_completed_job(job_id)
                
                return JobStatusResponse(
                    job_id=job_id,
                    status=JobStatus.COMPLETED if result.success else JobStatus.FAILED,
                    result=result,
                    metadata=metadata
                )
    except:
        pass
    
    # Job still running or not found
    return JobStatusResponse(
        job_id=job_id,
        status=JobStatus(metadata.get("status", "queued")),
        result=None,
        metadata=metadata
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint.
    
    IMPORTANT: This must be lightweight and return immediately.
    Do NOT make HTTP calls to workers here - the load balancer polls this
    endpoint with a short timeout (3s). If this hangs, the LB marks the
    scheduler as unhealthy and returns 503 for ALL requests.
    """
    return HealthResponse(
        status="healthy",
        service="Scheduler",
        timestamp=datetime.now(timezone.utc),
        details={
            "scheduling_mode": SCHEDULING_MODE.value,
            "workers_registered": len(worker_registry.worker_urls),
            "workers_cached": len(worker_registry._state_cache),
            "jobs_tracked": len(job_metadata),
            "active_assignments": len(job_assignments)
        }
    )


@app.get("/api/scheduler/assignments")
async def get_job_assignments():
    """Debug endpoint: view current job assignments and worker loads."""
    return {
        "job_assignments": job_assignments,
        "worker_load_map": worker_load_map,
        "total_jobs": len(job_metadata)
    }


@app.get("/api/scheduler/mode")
async def get_scheduler_mode():
    """Get current scheduling mode."""
    return {"mode": scheduler.mode.value}


@app.post("/api/scheduler/mode")
async def set_scheduler_mode(mode: str):
    """Change scheduling algorithm (for experimentation)."""
    try:
        new_mode = SchedulingMode(mode)
        scheduler.set_mode(new_mode)
        return {"mode": new_mode.value, "message": "Scheduling mode updated"}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")


# ============================================================================
# Background Tasks
# ============================================================================

async def cleanup_abandoned_jobs():
    """Background task to clean up abandoned jobs and reconcile worker load map."""
    while True:
        await asyncio.sleep(60)  # Run every 60 seconds
        
        try:
            now = datetime.now(timezone.utc)
            abandoned_jobs = []
            
            # Find jobs assigned more than 5 minutes ago
            for job_id, assignment in list(job_assignments.items()):
                assigned_at = assignment.get("assigned_at")
                if assigned_at:
                    age = (now - assigned_at).total_seconds()
                    if age > 300:  # 5 minutes
                        abandoned_jobs.append(job_id)
            
            # Clean up abandoned jobs
            for job_id in abandoned_jobs:
                print(f"[CLEANUP] Removing abandoned job {job_id}")
                cleanup_completed_job(job_id)
            
            if abandoned_jobs:
                print(f"[CLEANUP] Cleaned up {len(abandoned_jobs)} abandoned jobs")
        
        except Exception as e:
            print(f"[ERROR] Cleanup task error: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize scheduler on startup."""
    print("[OK] Scheduler server started")
    print(f"[WORKERS] Worker registry: {worker_registry}")
    
    # Start background cleanup task
    asyncio.create_task(cleanup_abandoned_jobs())
    print("[OK] Background cleanup task started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "DAALAB Scheduler Service",
        "version": "2.0.0",
        "scheduling_mode": SCHEDULING_MODE.value,
        "workers": len(worker_registry.worker_urls),
        "endpoints": {
            "submit_job": "POST /api/submit-job",
            "run_code_sync": "POST /api/run-code",
            "job_status": "GET /api/job/{job_id}",
            "health": "GET /api/health"
        }
    }


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("SCHEDULER_PORT", 8000))
    host = os.getenv("SCHEDULER_HOST", "0.0.0.0")
    
    print(f"[START] Starting scheduler on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
