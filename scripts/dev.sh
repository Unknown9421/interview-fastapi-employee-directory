#!/bin/bash
# ==============================================
# Development server script
# Runs with auto-reload enabled
# ==============================================

set -e

echo "🔧 Starting development server..."

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app
