#!/bin/bash
# ==============================================
# Database initialization script
# Creates migrations and seeds initial data
# ==============================================

set -e

# Force unbuffered output and redirect to stderr for Docker visibility
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

echo "🔍 Checking migrations directory: $MIGRATIONS_DIR"
echo "   Directory contents:"
ls -la $MIGRATIONS_DIR/
echo "   Found $MIGRATION_FILES .py file(s)"

if [ "$MIGRATION_FILES" -eq 0 ]; then
    echo "📝 No migrations found. Auto-generating initial migration..."

    # Debug: Show what alembic sees
    echo "   DEBUG: Testing alembic configuration..."
    python -c "
from app.database import Base
from app.models import Organization, OrganizationConfig, Employee
print('Models imported successfully')
print('Tables in metadata:', list(Base.metadata.tables.keys()))
"

    # Run autogenerate
    alembic revision --autogenerate -m "initial"
    AUTOGEN_RESULT=$?

    echo "   DEBUG: Autogenerate exit code: $AUTOGEN_RESULT"

    if [ $AUTOGEN_RESULT -eq 0 ]; then
        echo "✅ Initial migration created"
        # Show the created migration file
        CREATED_FILE=$(find $MIGRATIONS_DIR -maxdepth 1 -name "*.py" -type f | head -1)
        if [ -n "$CREATED_FILE" ]; then
            echo "📄 Migration file: $CREATED_FILE"
            echo "--- Migration content (first 80 lines) ---"
            head -80 "$CREATED_FILE"
            echo "--- End of preview ---"

            # Check if migration has actual operations
            if grep -q "op.create_table" "$CREATED_FILE"; then
                echo "✅ Migration contains create_table operations"
            else
                echo "⚠️  WARNING: Migration does NOT contain create_table operations!"
                echo "   This means alembic didn't detect any models."
                echo "   Full file content:"
                cat "$CREATED_FILE"
            fi
        else
            echo "❌ ERROR: Migration file was not created!"
            ls -la $MIGRATIONS_DIR/
        fi
    else
        echo "❌ Failed to create migration (exit code: $AUTOGEN_RESULT)"
        exit 1
    fi
else
    echo "📋 Found $MIGRATION_FILES existing migration(s)"
    ls -la $MIGRATIONS_DIR/*.py
    echo "   Migration file contents:"
    for f in $MIGRATIONS_DIR/*.py; do
        echo "=== $f ==="
        head -50 "$f"
    done
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
