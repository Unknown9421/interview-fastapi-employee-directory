from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.employees import router as employees_router
from app.middleware.rate_limiter import RateLimiter, RateLimitMiddleware

settings = get_settings()

# Initialize rate limiter
rate_limiter = RateLimiter(
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    await rate_limiter.start_cleanup_task()
    yield
    # Shutdown
    await rate_limiter.stop_cleanup_task()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Employee Search Service API

    A high-performance microservice for searching employees in an HR directory.

    ### Features:
    * **Multi-tenancy**: Strict data isolation between organizations
    * **Dynamic columns**: Configurable response fields per organization
    * **Rate limiting**: Custom implementation to prevent abuse
    * **Pagination**: Efficient handling of large datasets

    ### Authentication:
    Pass `X-Organization-ID` header with every request for multi-tenancy support.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

# Include routers
app.include_router(employees_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy"}
