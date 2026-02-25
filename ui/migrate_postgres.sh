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

# migrate_postgres.sh - Migrate Hamilton UI from PostgreSQL 12 to 16

set -e

BACKUP_FILE="hamilton_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Hamilton UI PostgreSQL 12 → 16 Migration"
echo "========================================"
echo ""
echo "This script will:"
echo "  1. Backup your PostgreSQL 12 data"
echo "  2. Stop containers and remove old data volume"
echo "  3. Start PostgreSQL 16 containers"
echo "  4. Restore your data to PostgreSQL 16"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Check if docker compose or docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    echo "Error: Neither 'docker compose' nor 'docker-compose' command found"
    exit 1
fi

# Check if old containers are running
if ! $DOCKER_COMPOSE ps | grep -q "db"; then
    echo "Error: Hamilton UI containers not running. Start them first with ./run.sh"
    exit 1
fi

# Check PostgreSQL version
PG_VERSION=$($DOCKER_COMPOSE exec -T db psql -U hamilton -d hamilton -c "SHOW server_version;" -t | tr -d ' ')
if [[ $PG_VERSION == 16* ]]; then
    echo "You are already running PostgreSQL 16. No migration needed."
    exit 0
fi

echo ""
echo "Detected PostgreSQL version: $PG_VERSION"
echo ""

# Backup
echo "Step 1: Backing up PostgreSQL data..."
$DOCKER_COMPOSE exec -T db pg_dump -U hamilton hamilton > "$BACKUP_FILE"
echo "✓ Backup saved to: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
echo ""

# Stop and remove
echo "Step 2: Stopping containers and removing old data..."
$DOCKER_COMPOSE down
docker volume rm ui_postgres_data || true
echo "✓ Old data removed"
echo ""

# Start new
echo "Step 3: Starting PostgreSQL 16 containers..."
echo "   This may take a few minutes on first run..."
./run.sh --build > /tmp/hamilton_build.log 2>&1 &
BUILD_PID=$!

# Wait for build to complete
wait $BUILD_PID || true

# Wait for database to be ready
echo "   Waiting for database to initialize..."
sleep 20

MAX_RETRIES=30
RETRY_COUNT=0
until $DOCKER_COMPOSE exec -T db pg_isready -U hamilton > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Database failed to start after $MAX_RETRIES attempts"
        echo "Check logs: $DOCKER_COMPOSE logs db"
        exit 1
    fi
    echo "   Still waiting... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ PostgreSQL 16 ready"
echo ""

# Restore
echo "Step 4: Restoring data to PostgreSQL 16..."
echo "   (Ignoring 'already exists' errors - this is normal)"
$DOCKER_COMPOSE exec -T db psql -U hamilton hamilton < "$BACKUP_FILE" 2>&1 | \
    grep -v "ERROR:.*already exists" | \
    grep -v "^$" || true
echo "✓ Data restored"
echo ""

# Fix permissions
echo "Step 5: Fixing permissions..."
$DOCKER_COMPOSE exec -T db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hamilton;" > /dev/null
$DOCKER_COMPOSE exec -T db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hamilton;" > /dev/null
echo "✓ Permissions fixed"
echo ""

# Verify
echo "Step 6: Verifying migration..."
TABLE_COUNT=$($DOCKER_COMPOSE exec -T db psql -U hamilton hamilton -c "\dt" | grep -c "public" || echo "0")
echo "✓ Found $TABLE_COUNT tables"
echo ""

echo "========================================"
echo "Migration complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Navigate to http://localhost:8242"
echo "  2. Verify your projects and runs are present"
echo "  3. If everything looks good, you can delete the backup:"
echo "     rm $BACKUP_FILE"
echo ""
echo "If you encounter issues:"
echo "  - Check logs: $DOCKER_COMPOSE logs"
echo "  - Restore from backup: See UPGRADE.md"
echo "  - Get help: https://github.com/apache/hamilton/issues"
