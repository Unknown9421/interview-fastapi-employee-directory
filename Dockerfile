# ============================================
# Stage 1: Builder - Install dependencies
# ============================================
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements first (better layer caching)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# ============================================
# Stage 2: Runtime - Minimal production image
# ============================================
FROM python:3.12-slim AS runtime

# OCI Labels for metadata
LABEL org.opencontainers.image.title="Employee Search Service" \
      org.opencontainers.image.description="FastAPI microservice for employee search directory" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Unknown9421" \
      org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Install only runtime dependencies (libpq for PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -d /app -s /sbin/nologin appuser

WORKDIR /app

# Copy application code (exclude unnecessary files via .dockerignore)
COPY --chown=appuser:appgroup . .

# Remove unnecessary files (keep tests for container testing)
RUN rm -rf \
    .git \
    .gitignore \
    .env* \
    docs/ \
    __pycache__ \
    *.pyc \
    .pytest_cache \
    .mypy_cache \
    .ruff_cache \
    Dockerfile \
    docker-compose.yml \
    2>/dev/null || true

# Make scripts executable
RUN chmod +x /app/scripts/*.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application using start.sh (handles migrations and seeding)
CMD ["/app/scripts/start.sh"]
