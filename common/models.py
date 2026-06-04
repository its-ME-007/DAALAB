"""Shared Pydantic models and data structures for scheduler-worker architecture."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Language(str, Enum):
    """Supported programming languages."""
    PYTHON = "python"
    CPP = "cpp"


class ComplexityClass(str, Enum):
    """Time complexity classifications."""
    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    QUADRATIC = "O(n^2)"
    CUBIC = "O(n^3)"
    EXPONENTIAL = "O(2^n)"
    FACTORIAL = "O(n!)"
    UNKNOWN = "UNKNOWN"


# ============================================================================
# Job Models
# ============================================================================

class JobRequest(BaseModel):
    """Request to execute code."""
    code: str = Field(..., description="Code to execute")
    language: Language = Field(default=Language.PYTHON, description="Programming language")
    algorithm_name: Optional[str] = Field(None, description="Algorithm name for tracking")
    input_size: Optional[int] = Field(None, description="Input size for complexity analysis")
    user_id: Optional[str] = Field(None, description="User ID from JWT token")
    complexity_hint: Optional[Dict[str, Any]] = Field(None, description="Pre-analyzed complexity from api_server")


class ComplexityAnalysis(BaseModel):
    """AI-derived complexity analysis."""
    time_complexity: str = Field(..., description="Time complexity (Big-O notation)")
    space_complexity: Optional[str] = Field(None, description="Space complexity")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    explanation: Optional[str] = Field(None, description="Complexity explanation")
    algorithm_detected: Optional[str] = Field(None, description="Detected algorithm name")


class JobMetadata(BaseModel):
    """Extended metadata for job scheduling."""
    job_id: str = Field(..., description="Unique job identifier")
    complexity_analysis: Optional[ComplexityAnalysis] = None
    estimated_cost_ms: float = Field(default=500.0, description="Estimated execution time in ms")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ExecutionRequest(BaseModel):
    """Request sent from scheduler to worker."""
    job_id: str
    code: str
    language: Language
    estimated_cost_ms: float = Field(default=500.0)
    user_id: Optional[str] = None
    algorithm_name: Optional[str] = None
    input_size: Optional[int] = None


class ExecutionResult(BaseModel):
    """Result from worker execution."""
    job_id: str
    success: bool
    output: str = ""
    error: Optional[str] = None
    actual_runtime_ms: float = 0.0
    exit_code: Optional[int] = None
    worker_id: str = ""
    completed_at: datetime = Field(default_factory=datetime.utcnow)


class JobResponse(BaseModel):
    """Response to client after job submission."""
    job_id: str
    status: JobStatus
    message: str = ""
    estimated_wait_time_ms: Optional[float] = None
    selected_worker_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response for job status queries."""
    job_id: str
    status: JobStatus
    result: Optional[ExecutionResult] = None
    metadata: Optional[JobMetadata] = None


# ============================================================================
# Worker Models
# ============================================================================

class WorkerState(BaseModel):
    """Current state of a worker."""
    worker_id: str = Field(..., description="Unique worker identifier")
    queue_cost_ms: float = Field(default=0.0, description="Total estimated cost in queue")
    active_jobs: int = Field(default=0, description="Number of jobs currently executing")
    cpu_util: Optional[float] = Field(None, ge=0.0, le=1.0, description="CPU utilization (0-1)")
    mem_util: Optional[float] = Field(None, ge=0.0, le=1.0, description="Memory utilization (0-1)")
    is_healthy: bool = Field(default=True, description="Worker health status")
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)


class WorkerRegistration(BaseModel):
    """Worker registration information."""
    worker_id: str
    worker_url: str
    supported_languages: List[Language] = Field(default_factory=lambda: [Language.PYTHON, Language.CPP])
    max_concurrent_jobs: int = Field(default=10)


# ============================================================================
# Scheduler Models
# ============================================================================

class SchedulingMode(str, Enum):
    """Scheduling algorithm selection."""
    QUEUE_LENGTH = "queue_length"  # Baseline: Select by active_jobs count
    QUEUE_COST = "queue_cost"      # Proposed: Select by estimated cost
    RANDOM = "random"              # Baseline: uniform random healthy worker
    ROUND_ROBIN = "round_robin"    # Baseline: cyclic, ignores load entirely


class SchedulingDecision(BaseModel):
    """Result of scheduling algorithm."""
    selected_worker_id: str
    selected_worker_url: str
    scheduling_mode: SchedulingMode
    decision_time_ms: float
    worker_state_at_decision: WorkerState
    reasoning: Optional[str] = None


# ============================================================================
# API Response Models (Compatible with existing frontend)
# ============================================================================

class CodeResponse(BaseModel):
    """Legacy response format for backward compatibility."""
    output: str
    runtime: float
    success: bool
    error: Optional[str] = None
    saved_to_db: bool = False
    job_id: Optional[str] = None  # New field for async tracking


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Optional[Dict[str, Any]] = None
