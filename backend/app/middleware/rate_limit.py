"""
Rate Limiting Middleware

Implements sliding window rate limiting to prevent API abuse.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import asyncio
from common.config import settings
from common.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Thread-safe sliding window rate limiter.
    
    Uses in-memory storage - for production with multiple instances,
    consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> tuple[bool, int]:
        """
        Check if a request from client_id is allowed.
        
        Args:
            client_id: Unique identifier for the client (IP or user ID)
            
        Returns:
            tuple: (is_allowed: bool, remaining_requests: int)
        """
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds
            
            # Clean old requests outside the window
            self.requests[client_id] = [
                t for t in self.requests[client_id] 
                if t > window_start
            ]
            
            current_count = len(self.requests[client_id])
            remaining = max(0, self.max_requests - current_count)
            
            if current_count >= self.max_requests:
                return False, 0
            
            # Record this request
            self.requests[client_id].append(now)
            return True, remaining - 1
    
    async def cleanup(self):
        """Remove stale entries to prevent memory leaks."""
        async with self._lock:
            now = time.time()
            window_start = now - self.window_seconds
            stale_keys = []
            
            for key, timestamps in self.requests.items():
                # Remove clients with no recent requests
                if not timestamps or max(timestamps) < window_start:
                    stale_keys.append(key)
            
            for key in stale_keys:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_PER_MINUTE,
    window_seconds=60
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting requests.
    """
    
    # Paths that should bypass rate limiting
    BYPASS_PATHS = {"/health", "/", "/docs", "/openapi.json", "/redoc"}
    
    async def dispatch(self, request: Request, call_next):
        # Bypass health checks and docs
        if request.url.path in self.BYPASS_PATHS:
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        is_allowed, remaining = await rate_limiter.is_allowed(client_ip)
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(settings.RATE_LIMIT_PER_MINUTE),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP, considering proxy headers.
        """
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the first IP (original client)
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
