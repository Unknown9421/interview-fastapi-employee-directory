from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from app.core.config import settings
from app.middleware.rate_limiter import RateLimiterMiddleware, rate_limiter
from app.routers import (
    organizations_router,
    employees_router,
    dynamic_columns_router,
    api_keys_router,
    admin_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Start background task for rate limiter cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("Application shutdown complete")


async def periodic_cleanup():
    """Periodically clean up expired rate limiter entries."""
    while True:
        try:
            await asyncio.sleep(60)  # Run every minute
            await rate_limiter.cleanup_all()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error in rate limiter cleanup: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Employee Directory API

High-performance Employee Search Microservice with:

- **Dynamic column configuration** per organization
- **Multi-tenancy security** via API key authentication
- **Custom in-memory rate limiting** (no external libraries)
- **Optimized for millions of records**

### Authentication

All endpoints (except /admin and /health) require an API key in the `X-API-Key` header.

### Rate Limiting

- Default: 100 requests per 60 seconds per API key/IP
- Headers returned: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
""",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimiterMiddleware)

# Include routers
app.include_router(admin_router)
app.include_router(organizations_router)
app.include_router(employees_router)
app.include_router(dynamic_columns_router)
app.include_router(api_keys_router)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - basic API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
