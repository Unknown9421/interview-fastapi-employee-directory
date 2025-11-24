#!/bin/bash
# ==============================================
# Test runner script
# ==============================================

set -e

echo "🧪 Running tests..."

# Run pytest with coverage
pytest \
    --verbose \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    "$@"

echo "✅ Tests completed"
echo "📊 Coverage report: htmlcov/index.html"
