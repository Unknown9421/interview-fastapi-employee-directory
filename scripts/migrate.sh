#!/bin/bash
# ==============================================
# Migration helper script
# Usage: ./scripts/migrate.sh [command] [message]
# ==============================================

set -e

COMMAND=${1:-"upgrade"}
MESSAGE=${2:-"auto migration"}

case $COMMAND in
    "create"|"new"|"make")
        echo "📝 Creating new migration: $MESSAGE"
        alembic revision --autogenerate -m "$MESSAGE"
        echo "✅ Migration created"
        ;;

    "upgrade"|"up")
        echo "⬆️  Running migrations..."
        alembic upgrade head
        echo "✅ Migrations applied"
        ;;

    "downgrade"|"down")
        echo "⬇️  Rolling back last migration..."
        alembic downgrade -1
        echo "✅ Rollback complete"
        ;;

    "reset")
        echo "🔄 Resetting database..."
        alembic downgrade base
        alembic upgrade head
        echo "✅ Database reset complete"
        ;;

    "history")
        echo "📋 Migration history:"
        alembic history --verbose
        ;;

    "current")
        echo "📍 Current migration:"
        alembic current
        ;;

    *)
        echo "Usage: $0 [command] [message]"
        echo ""
        echo "Commands:"
        echo "  create <message>  - Create new migration"
        echo "  upgrade           - Apply all pending migrations"
        echo "  downgrade         - Rollback last migration"
        echo "  reset             - Reset and reapply all migrations"
        echo "  history           - Show migration history"
        echo "  current           - Show current migration"
        exit 1
        ;;
esac
