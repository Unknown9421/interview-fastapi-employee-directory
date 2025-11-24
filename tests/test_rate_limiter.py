import pytest
import asyncio
import time

from app.middleware.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_within_limit():
    """Test that rate limiter allows requests within the limit."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    for i in range(5):
        allowed, headers = await limiter.is_allowed("test_client")
        assert allowed is True
        assert "X-RateLimit-Limit" in headers
        assert headers["X-RateLimit-Limit"] == "5"


@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess_requests():
    """Test that rate limiter blocks requests over the limit."""
    limiter = RateLimiter(max_requests=3, window_seconds=60)

    # Make 3 allowed requests
    for _ in range(3):
        allowed, _ = await limiter.is_allowed("test_client")
        assert allowed is True

    # 4th request should be blocked
    allowed, headers = await limiter.is_allowed("test_client")
    assert allowed is False
    assert "X-RateLimit-Reset" in headers
    assert "Retry-After" in headers


@pytest.mark.asyncio
async def test_rate_limiter_different_clients():
    """Test that rate limiter tracks different clients separately."""
    limiter = RateLimiter(max_requests=2, window_seconds=60)

    # Client A makes 2 requests
    for _ in range(2):
        allowed, _ = await limiter.is_allowed("client_a")
        assert allowed is True

    # Client A should be blocked
    allowed, _ = await limiter.is_allowed("client_a")
    assert allowed is False

    # Client B should still be allowed
    allowed, _ = await limiter.is_allowed("client_b")
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_window_reset():
    """Test that rate limiter resets after window expires."""
    limiter = RateLimiter(max_requests=2, window_seconds=1)

    # Make 2 requests
    for _ in range(2):
        allowed, _ = await limiter.is_allowed("test_client")
        assert allowed is True

    # Should be blocked
    allowed, _ = await limiter.is_allowed("test_client")
    assert allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Should be allowed again
    allowed, _ = await limiter.is_allowed("test_client")
    assert allowed is True


@pytest.mark.asyncio
async def test_rate_limiter_remaining_count():
    """Test that remaining count is correctly calculated."""
    limiter = RateLimiter(max_requests=5, window_seconds=60)

    # First request
    allowed, headers = await limiter.is_allowed("test_client")
    assert allowed is True
    assert headers["X-RateLimit-Remaining"] == "4"

    # Second request
    allowed, headers = await limiter.is_allowed("test_client")
    assert allowed is True
    assert headers["X-RateLimit-Remaining"] == "3"


@pytest.mark.asyncio
async def test_rate_limiter_cleanup():
    """Test that cleanup task removes stale entries."""
    limiter = RateLimiter(max_requests=5, window_seconds=1)

    # Make a request
    await limiter.is_allowed("test_client")

    # Verify entry exists
    assert "test_client" in limiter._requests

    # Wait for window + cleanup
    await asyncio.sleep(1.5)

    # Manually trigger cleanup
    await limiter._cleanup_stale_entries()

    # Entry should be removed
    assert "test_client" not in limiter._requests


@pytest.mark.asyncio
async def test_rate_limiter_concurrent_requests():
    """Test rate limiter with concurrent requests."""
    limiter = RateLimiter(max_requests=10, window_seconds=60)

    async def make_request(client_id: str):
        return await limiter.is_allowed(client_id)

    # Make 10 concurrent requests
    tasks = [make_request("concurrent_client") for _ in range(10)]
    results = await asyncio.gather(*tasks)

    # All 10 should be allowed
    allowed_count = sum(1 for allowed, _ in results if allowed)
    assert allowed_count == 10

    # 11th request should be blocked
    allowed, _ = await limiter.is_allowed("concurrent_client")
    assert allowed is False
