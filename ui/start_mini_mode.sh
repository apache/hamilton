#!/bin/bash
# Start Hamilton UI in mini mode for local testing

set -e

echo "🚀 Starting Hamilton UI in Mini Mode"
echo "===================================="
echo ""

# Check if PostgreSQL container is running
if ! docker ps --format '{{.Names}}' | grep -q "^hamilton-ui-db$"; then
    echo "📦 Starting PostgreSQL container..."
    docker run -d \
        --name hamilton-ui-db \
        -e POSTGRES_DB=hamilton \
        -e POSTGRES_USER=hamilton \
        -e POSTGRES_PASSWORD=hamilton \
        -p 5433:5432 \
        postgres:12

    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 5

    # Wait for PostgreSQL to accept connections
    until docker exec hamilton-ui-db pg_isready -U hamilton; do
        echo "Waiting for database..."
        sleep 2
    done
    echo "✅ PostgreSQL is ready"
else
    echo "✅ PostgreSQL container already running"
fi

echo ""
echo "📝 Setting up environment variables..."

# Export environment variables for mini mode
export HAMILTON_ENV=mini
export DB_HOST=localhost
export DB_PORT=5433
export DB_NAME=hamilton
export DB_USER=hamilton
export DB_PASSWORD=hamilton
export HAMILTON_BLOB_STORE=local
export HAMILTON_LOCAL_BLOB_DIR=$(pwd)/ui/backend/server/blobs
export DJANGO_SECRET_KEY=mini-mode-secret-key-for-testing-only
export DJANGO_DEBUG=True
export HAMILTON_AUTH_MODE=permissive
export HAMILTON_PERMISSIVE_MODE_GLOBAL_KEY=test-key

echo "✅ Environment configured"
echo ""

# Create blob directory if it doesn't exist
mkdir -p "$HAMILTON_LOCAL_BLOB_DIR"

echo "🔧 Running database migrations..."
cd ui/backend/server
python manage.py migrate

echo ""
echo "✨ Starting Hamilton UI server..."
echo ""
echo "   URL: http://localhost:8241"
echo "   Auth: Permissive mode (no login required)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
python manage.py runserver 0.0.0.0:8241
