#!/bin/bash
# ==============================================
# Application startup script
# Initializes database and starts the server
# ==============================================

set -e

# Force unbuffered output and redirect to stderr for Docker visibility
exec 1>&2

echo "🚀 Starting Employee Search Service..."

# Initialize database
/app/scripts/init-db.sh

# Start uvicorn server
echo "🌐 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
