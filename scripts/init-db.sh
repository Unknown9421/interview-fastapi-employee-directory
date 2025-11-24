#!/bin/sh
# ==============================================
# Database initialization script
# Creates migrations and seeds initial data
# ==============================================

set -e

# Redirect output to stderr for Docker visibility
exec 1>&2

echo "🚀 Initializing database..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "
import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
        return True

asyncio.run(check())
" 2>/dev/null; then
        echo "✅ Database connection established"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - Retrying in 2 seconds..."
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "❌ Failed to connect to database after $MAX_RETRIES attempts"
    exit 1
fi

# Check if migrations exist, if not auto-generate
MIGRATIONS_DIR="/app/alembic/versions"
MIGRATION_FILES=$(find $MIGRATIONS_DIR -maxdepth 1 -name "*.py" -type f 2>/dev/null | wc -l)

if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "📝 No migrations found. Auto-generating initial migration..."
    alembic revision --autogenerate -m "initial"

    if [ $? -eq 0 ]; then
        echo "✅ Initial migration created"
    else
        echo "❌ Failed to create migration"
        exit 1
    fi
else
    echo "📋 Found $MIGRATION_FILES existing migration(s)"
fi

# Run migrations
echo "📦 Running database migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration failed"
    exit 1
fi

# Seed data
echo "🌱 Seeding database with sample data..."
python -m app.seed_data

if [ $? -eq 0 ]; then
    echo "✅ Database seeding completed"
else
    echo "❌ Seeding failed"
    exit 1
fi

echo "🎉 Database initialization complete!"
