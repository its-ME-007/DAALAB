"""Shared constants across all services."""

import os

# ============================================================================
# Scheduling Constants
# ============================================================================

# Language execution time multipliers (relative to C++)
LANGUAGE_MULTIPLIER = {
    "python": 4.0,  # Python is ~4x slower than C++
    "cpp": 1.0,     # C++ baseline
}

# Default execution cost when complexity is unknown
DEFAULT_COST_MS = 500.0

# CPU utilization threshold for applying penalty
CPU_OVERLOAD_THRESHOLD = 0.85

# Penalty added to queue cost for overloaded workers (in ms)
CPU_PENALTY = 1000.0

# Minimum confidence for a static-analysis complexity result to be trusted
# without falling back to the LLM. Results below this are treated as a miss.
STATIC_CONFIDENCE_THRESHOLD = 0.6

# ============================================================================
# Complexity Growth Functions (Base Costs in ms)
# ============================================================================

COMPLEXITY_BASE_COST = {
    "O(1)": 10.0,
    "O(log n)": 50.0,
    "O(n)": 100.0,
    "O(n log n)": 200.0,
    "O(n^2)": 500.0,
    "O(n^3)": 1000.0,
    "O(2^n)": 5000.0,
    "O(n!)": 10000.0,
    "UNKNOWN": DEFAULT_COST_MS,
}

# ============================================================================
# Worker Configuration
# ============================================================================

# Maximum concurrent jobs per worker (env-overridable so it can be swept as an
# experiment knob without code changes; consumed by the worker semaphore).
MAX_CONCURRENT_JOBS = int(os.getenv("MAX_CONCURRENT_JOBS", "10"))

# Worker health check timeout (seconds)
WORKER_HEALTH_TIMEOUT = 3.0

# Worker state cache TTL (seconds)
WORKER_STATE_CACHE_TTL = 3.0

# Docker execution timeout (seconds)
DOCKER_EXECUTION_TIMEOUT = 30.0

# ============================================================================
# Service URLs (Default - Override with Environment Variables)
# ============================================================================

DEFAULT_SCHEDULER_PORT = 8000
DEFAULT_WORKER_PORT = 8001
DEFAULT_AI_SERVICE_PORT = 8002
DEFAULT_LOAD_BALANCER_PORT = 8080

# ============================================================================
# Logging Configuration
# ============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
