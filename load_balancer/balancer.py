"""Simple load balancer for distributing traffic across schedulers.

This service provides:
1. Round-robin load balancing across schedulers
2. Health checking of scheduler instances
3. Automatic failover for unhealthy schedulers
4. Request forwarding without modification

Note: This load balancer is INTENTIONALLY SIMPLE and has NO awareness of:
- Code complexity
- Worker states
- Job costs
- Scheduling algorithms

Its sole purpose is traffic distribution and fault tolerance.
"""

import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List
from datetime import datetime, timezone
import asyncio
from itertools import cycle
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Configuration
# ============================================================================

# Get scheduler URLs from environment
SCHEDULER_URLS_STR = os.getenv("SCHEDULER_URLS", "http://localhost:8000")
SCHEDULER_URLS = [url.strip() for url in SCHEDULER_URLS_STR.split(",")]

# Health check interval (seconds)
HEALTH_CHECK_INTERVAL = 10.0

# Request timeout (seconds)
REQUEST_TIMEOUT = 60.0


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan with async context manager."""
    # Startup
    print("[BALANCER] Load balancer initialized")
    print(f"[POOL] Scheduler pool: {SCHEDULER_URLS}")
    
    # Initialize pool
    global pool
    pool = SchedulerPool(SCHEDULER_URLS)
    
    # Start health monitoring
    print("[MONITOR] Starting health monitor...")
    health_task = asyncio.create_task(health_monitor())
    
    # Initial health check
    await pool.update_health_status()
    
    yield
    
    # Shutdown
    print("[SHUTDOWN] Shutting down load balancer...")
    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    await pool.http_client.aclose()


app = FastAPI(
    title="DAALAB Load Balancer",
    description="Round-robin load balancer for scheduler instances",
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
# Scheduler Health Management
# ============================================================================

class SchedulerPool:
    """Manage pool of scheduler instances with health tracking."""
    
    def __init__(self, scheduler_urls: List[str]):
        self.all_schedulers = scheduler_urls
        self.healthy_schedulers = list(scheduler_urls)
        self.round_robin = cycle(self.healthy_schedulers)
        self.http_client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT)
    
    async def check_scheduler_health(self, scheduler_url: str) -> bool:
        """Check if a scheduler is healthy."""
        try:
            response = await self.http_client.get(
                f"{scheduler_url}/api/health",
                timeout=3.0
            )
            return response.status_code == 200
        except:
            return False
    
    async def update_health_status(self):
        """Update health status of all schedulers."""
        health_checks = [
            self.check_scheduler_health(url) for url in self.all_schedulers
        ]
        results = await asyncio.gather(*health_checks)
        
        # Update healthy scheduler list
        new_healthy = [
            url for url, is_healthy in zip(self.all_schedulers, results)
            if is_healthy
        ]
        
        if new_healthy != self.healthy_schedulers:
            print(f"[HEALTH] Health status changed:")
            print(f"   Healthy: {new_healthy}")
            self.healthy_schedulers = new_healthy
            self.round_robin = cycle(self.healthy_schedulers)
    
    def get_next_scheduler(self) -> str:
        """Get next scheduler using round-robin."""
        if not self.healthy_schedulers:
            raise HTTPException(
                status_code=503,
                detail="No healthy schedulers available"
            )
        
        return next(self.round_robin)
    
    async def forward_request(
        self,
        scheduler_url: str,
        method: str,
        path: str,
        headers: dict,
        body: bytes = None,
        query_params: dict = None
    ) -> Response:
        """
        Forward request to scheduler.
        
        Args:
            scheduler_url: Base URL of scheduler
            method: HTTP method
            path: Request path
            headers: Request headers
            body: Request body
            query_params: Query parameters
        
        Returns:
            FastAPI Response object
        """
        url = f"{scheduler_url}{path}"
        
        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                params=query_params
            )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to forward request to scheduler: {str(e)}"
            )


# Declare pool as global variable (will be initialized in lifespan)
pool: SchedulerPool = None


# ============================================================================
# Background Health Monitoring
# ============================================================================

async def health_monitor():
    """Background task to periodically check scheduler health."""
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        await pool.update_health_status()


# ============================================================================
# Load Balancing Endpoints
# ============================================================================

@app.get("/lb/health")
async def health_check():
    """
    Load balancer health check (separate from scheduler health).
    """
    return {
        "status": "healthy",
        "service": "Load Balancer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": {
            "total_schedulers": len(pool.all_schedulers),
            "healthy_schedulers": len(pool.healthy_schedulers),
            "scheduler_urls": pool.healthy_schedulers
        }
    }


@app.get("/lb/status")
async def get_status():
    """Get detailed load balancer status."""
    return {
        "service": "DAALAB Load Balancer",
        "algorithm": "round-robin",
        "schedulers": {
            "total": len(pool.all_schedulers),
            "healthy": len(pool.healthy_schedulers),
            "urls": pool.healthy_schedulers
        },
        "monitoring": {
            "health_check_interval_seconds": HEALTH_CHECK_INTERVAL,
            "request_timeout_seconds": REQUEST_TIMEOUT
        }
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_request(path: str, request: Request):
    """
    Proxy all requests to schedulers using round-robin.
    
    This is the core load balancing logic - simple and intentional:
    1. Select next scheduler (round-robin)
    2. Forward request without modification
    3. Return response directly
    
    NO complexity awareness, NO scheduling logic, NO job inspection.
    """
    # Get next scheduler
    scheduler_url = pool.get_next_scheduler()
    
    # Read request body
    body = await request.body()
    
    # Forward request
    response = await pool.forward_request(
        scheduler_url=scheduler_url,
        method=request.method,
        path=f"/{path}",
        headers=dict(request.headers),
        body=body,
        query_params=dict(request.query_params)
    )
    
    return response


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("LOAD_BALANCER_PORT", 8080))
    host = os.getenv("LOAD_BALANCER_HOST", "0.0.0.0")
    
    print(f"[START] Starting load balancer on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
