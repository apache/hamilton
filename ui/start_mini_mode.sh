#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

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
        postgres:18

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
uv run python manage.py migrate

echo ""
echo "✨ Starting Hamilton UI server..."
echo ""
echo "   URL: http://localhost:8241"
echo "   Auth: Permissive mode (no login required)"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
uv run python manage.py runserver 0.0.0.0:8241
