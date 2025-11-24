import time
import asyncio
from collections import defaultdict
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimiter:
    """
    Thread-safe sliding window rate limiter implementation.
    Uses only Python standard library as per requirements.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup_task(self):
        """Start background cleanup task to prevent memory leaks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_task(self):
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_loop(self):
        """Periodically clean up stale entries."""
        while True:
            await asyncio.sleep(self.window_seconds)
            await self._cleanup_stale_entries()

    async def _cleanup_stale_entries(self):
        """Remove entries older than the window."""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            keys_to_delete = []
            for key, timestamps in self._requests.items():
                # Remove old timestamps
                self._requests[key] = [ts for ts in timestamps if ts > cutoff_time]
                if not self._requests[key]:
                    keys_to_delete.append(key)

            # Remove empty keys
            for key in keys_to_delete:
                del self._requests[key]

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed for the given identifier.
        Returns (allowed, headers_dict).
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Get existing timestamps and filter old ones
            timestamps = self._requests[identifier]
            valid_timestamps = [ts for ts in timestamps if ts > cutoff_time]

            # Calculate remaining requests
            remaining = self.max_requests - len(valid_timestamps)

            # Prepare rate limit headers
            headers = {
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": str(max(0, remaining - 1) if remaining > 0 else 0),
                "X-RateLimit-Window": str(self.window_seconds),
            }

            if remaining <= 0:
                # Calculate reset time
                if valid_timestamps:
                    oldest = min(valid_timestamps)
                    reset_time = int(oldest + self.window_seconds)
                else:
                    reset_time = int(current_time + self.window_seconds)
                headers["X-RateLimit-Reset"] = str(reset_time)
                headers["Retry-After"] = str(reset_time - int(current_time))
                return False, headers

            # Add current request timestamp
            valid_timestamps.append(current_time)
            self._requests[identifier] = valid_timestamps

            return True, headers


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting requests.
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP address or organization ID from header)
        client_id = self._get_client_identifier(request)

        # Check rate limit
        allowed, headers = await self.rate_limiter.is_allowed(client_id)

        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": headers.get("Retry-After", "60"),
                }
            )
            for key, value in headers.items():
                response.headers[key] = value
            return response

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        Uses X-Organization-ID header if present, otherwise falls back to IP.
        """
        # Check for organization ID in header
        org_id = request.headers.get("X-Organization-ID")
        if org_id:
            return f"org:{org_id}"

        # Fall back to client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"

        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
