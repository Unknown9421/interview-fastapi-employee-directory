import time
import asyncio
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class RateLimiter:
    """
    Custom in-memory rate limiter using sliding window algorithm.
    No external libraries - pure Python implementation.
    """

    def __init__(self, requests_limit: int = None, window_seconds: int = None):
        self.requests_limit = requests_limit or settings.RATE_LIMIT_REQUESTS
        self.window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW_SECONDS

        # Store: {client_key: [(timestamp1, count1), (timestamp2, count2), ...]}
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()

    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Try to get API key from header first
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"api:{api_key[:16]}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        return f"ip:{client_ip}"

    async def _cleanup_old_requests(self, client_key: str, current_time: float):
        """Remove expired timestamps from the sliding window."""
        cutoff_time = current_time - self.window_seconds
        self._requests[client_key] = [
            ts for ts in self._requests[client_key]
            if ts > cutoff_time
        ]

    async def check_rate_limit(self, request: Request) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        Returns: (is_allowed, remaining_requests, reset_time)
        """
        async with self._lock:
            current_time = time.time()
            client_key = self._get_client_key(request)

            # Cleanup old requests
            await self._cleanup_old_requests(client_key, current_time)

            # Count current requests
            request_count = len(self._requests[client_key])

            if request_count >= self.requests_limit:
                # Calculate reset time
                oldest_request = min(self._requests[client_key]) if self._requests[client_key] else current_time
                reset_time = int(oldest_request + self.window_seconds - current_time)
                return False, 0, max(reset_time, 1)

            # Add current request
            self._requests[client_key].append(current_time)

            remaining = self.requests_limit - request_count - 1
            reset_time = int(self.window_seconds)

            return True, remaining, reset_time

    async def cleanup_all(self):
        """Periodic cleanup of all expired entries."""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            keys_to_delete = []
            for client_key in self._requests:
                self._requests[client_key] = [
                    ts for ts in self._requests[client_key]
                    if ts > cutoff_time
                ]
                if not self._requests[client_key]:
                    keys_to_delete.append(client_key)

            for key in keys_to_delete:
                del self._requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to all requests."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        is_allowed, remaining, reset_time = await rate_limiter.check_rate_limit(request)

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": reset_time,
                    "message": f"Too many requests. Please try again in {reset_time} seconds."
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(rate_limiter.requests_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time)
                }
            )

        response = await call_next(request)

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.requests_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response
