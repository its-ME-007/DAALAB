"""Worker registry and discovery for scheduler.

This module manages the pool of available workers and fetches their current
state for scheduling decisions.
"""

import os
import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime, timezone
from datetime import datetime, timedelta
from common.models import WorkerState, WorkerRegistration, Language
from common.constants import WORKER_HEALTH_TIMEOUT, WORKER_STATE_CACHE_TTL


class WorkerRegistry:
    """
    Registry of available workers with health checking and state caching.
    
    Responsibilities:
    - Maintain list of registered workers
    - Fetch worker states on demand
    - Cache worker states to reduce polling overhead
    - Track worker health status
    """
    
    def __init__(self, worker_urls: Optional[List[str]] = None):
        """
        Initialize worker registry.
        
        Args:
            worker_urls: List of worker URLs. If None, reads from environment
                        variable WORKER_URLS (comma-separated)
        """
        if worker_urls is None:
            worker_urls_str = os.getenv("WORKER_URLS", "http://localhost:8001")
            worker_urls = [url.strip() for url in worker_urls_str.split(",")]
        
        self.worker_urls = worker_urls
        self._state_cache: Dict[str, tuple[WorkerState, datetime]] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=WORKER_HEALTH_TIMEOUT)
        return self._http_client
    
    async def fetch_worker_state(self, worker_url: str) -> Optional[WorkerState]:
        """
        Fetch current state from a single worker.
        
        Args:
            worker_url: Base URL of worker service
        
        Returns:
            WorkerState or None if worker is unreachable
        """
        try:
            client = await self._get_http_client()
            response = await client.get(f"{worker_url}/status")
            response.raise_for_status()
            
            state_data = response.json()
            return WorkerState(**state_data)
        
        except Exception as e:
            print(f"[WARNING] Failed to fetch state from {worker_url}: {e}")
            return None
    
    async def fetch_all_worker_states(
        self,
        use_cache: bool = True
    ) -> List[WorkerState]:
        """
        Fetch current state from all registered workers.
        
        Args:
            use_cache: Whether to use cached states (if fresh)
        
        Returns:
            List of WorkerState objects for healthy workers
        """
        states = []
        now = datetime.now(timezone.utc)
        
        # Fetch states concurrently
        tasks = []
        for worker_url in self.worker_urls:
            # Check cache first
            if use_cache and worker_url in self._state_cache:
                cached_state, cached_at = self._state_cache[worker_url]
                age = (now - cached_at).total_seconds()
                
                if age < WORKER_STATE_CACHE_TTL:
                    states.append(cached_state)
                    continue
            
            # Cache miss or expired - fetch fresh state
            tasks.append(self.fetch_worker_state(worker_url))
        
        # Wait for all fetches to complete
        if tasks:
            fetched_states = await asyncio.gather(*tasks, return_exceptions=True)
            
            for worker_url, state in zip(self.worker_urls, fetched_states):
                if isinstance(state, WorkerState):
                    # Update cache
                    self._state_cache[worker_url] = (state, now)
                    states.append(state)
        
        return states
    
    async def check_worker_health(self, worker_url: str) -> bool:
        """
        Check if a worker is healthy.
        
        Args:
            worker_url: Base URL of worker service
        
        Returns:
            True if worker responds to /health endpoint
        """
        try:
            client = await self._get_http_client()
            response = await client.get(f"{worker_url}/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_healthy_workers(self) -> List[str]:
        """
        Get list of healthy worker URLs.
        
        Returns:
            List of worker URLs that pass health check
        """
        health_checks = [
            self.check_worker_health(url) for url in self.worker_urls
        ]
        results = await asyncio.gather(*health_checks)
        
        return [
            url for url, is_healthy in zip(self.worker_urls, results)
            if is_healthy
        ]
    
    def register_worker(self, worker_url: str) -> None:
        """
        Register a new worker dynamically.
        
        Args:
            worker_url: Base URL of worker service
        """
        if worker_url not in self.worker_urls:
            self.worker_urls.append(worker_url)
            print(f"[OK] Registered worker: {worker_url}")
    
    def unregister_worker(self, worker_url: str) -> None:
        """
        Remove a worker from the registry.
        
        Args:
            worker_url: Base URL of worker service
        """
        if worker_url in self.worker_urls:
            self.worker_urls.remove(worker_url)
            if worker_url in self._state_cache:
                del self._state_cache[worker_url]
            print(f"[INFO] Unregistered worker: {worker_url}")
    
    def clear_cache(self) -> None:
        """Clear all cached worker states."""
        self._state_cache.clear()
    
    async def close(self) -> None:
        """Close HTTP client resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None
    
    def __len__(self) -> int:
        """Get number of registered workers."""
        return len(self.worker_urls)
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"WorkerRegistry(workers={len(self.worker_urls)}, urls={self.worker_urls})"


# ============================================================================
# Global Registry Instance
# ============================================================================

# Singleton instance for use across scheduler modules
_global_registry: Optional[WorkerRegistry] = None


def get_worker_registry() -> WorkerRegistry:
    """
    Get global worker registry instance.
    
    Creates instance on first call using WORKER_URLS environment variable.
    
    Returns:
        WorkerRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = WorkerRegistry()
    return _global_registry


# ============================================================================
# Testing and Diagnostics
# ============================================================================

async def test_registry():
    """Test worker registry functionality."""
    print("Testing WorkerRegistry...")
    
    # Create registry with mock workers
    registry = WorkerRegistry([
        "http://localhost:8001",
        "http://localhost:8002",
    ])
    
    print(f"\n{registry}")
    
    print("\n🔍 Checking worker health...")
    healthy_workers = await registry.get_healthy_workers()
    print(f"Healthy workers: {healthy_workers}")
    
    print("\n[INFO] Fetching worker states...")
    states = await registry.fetch_all_worker_states(use_cache=False)
    
    if states:
        for state in states:
            print(f"  - {state.worker_id}: {state.active_jobs} jobs, {state.queue_cost_ms}ms queue")
    else:
        print("  No workers available (expected if workers not running)")
    
    print("\n[OK] Registry test complete!")
    await registry.close()


if __name__ == "__main__":
    asyncio.run(test_registry())
