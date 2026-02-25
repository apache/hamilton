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

# migrate_postgres_simple.sh - Migrate Hamilton UI from PostgreSQL 12 to 18
# Uses Django's dumpdata/loaddata for safe, validated migration

set -euo pipefail

BACKUP_FILE="hamilton_migration_$(date +%Y%m%d_%H%M%S).json"

echo "Hamilton UI PostgreSQL 12 → 18 Migration"
echo "========================================="
echo ""
echo "This script will:"
echo "  1. Export your Hamilton data using Django"
echo "  2. Stop containers and remove PostgreSQL 12 volume"
echo "  3. Start PostgreSQL 18 containers"
echo "  4. Restore your Hamilton data"
echo ""

# Check if docker compose or docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
else
    echo "Error: Neither 'docker compose' nor 'docker-compose' found"
    exit 1
fi

# Check if containers are running
if ! $DOCKER_COMPOSE ps --services --filter "status=running" | grep -q "backend"; then
    echo "Error: Hamilton UI containers not running"
    echo "Start them first: ./run.sh"
    exit 1
fi

# Check PostgreSQL version
echo "Checking current PostgreSQL version..."
PG_VERSION=$($DOCKER_COMPOSE exec -T db psql -U hamilton -d hamilton -At -c "SHOW server_version;" | cut -d. -f1)

if [ "$PG_VERSION" -ge 18 ]; then
    echo "Already on PostgreSQL $PG_VERSION. No migration needed."
    exit 0
fi

if [ "$PG_VERSION" -lt 12 ]; then
    echo "Error: PostgreSQL $PG_VERSION detected"
    echo "This script handles PostgreSQL 12+ → 18"
    echo "Manual upgrade required for older versions"
    exit 1
fi

echo "Current version: PostgreSQL $PG_VERSION"
echo ""

read -p "Continue with migration? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "================================================================"
echo "Step 1: Exporting Hamilton data"
echo "================================================================"
echo ""

# Use the backup script
if ! ./backup_hamilton_data.sh "$BACKUP_FILE"; then
    echo "Error: Data export failed"
    exit 1
fi

# Verify backup was created and has content
if [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file is empty or missing"
    exit 1
fi

RECORD_COUNT=$(uv run python -c "import json; print(len(json.load(open('$BACKUP_FILE'))))")
if [ "$RECORD_COUNT" -eq 0 ]; then
    echo "Warning: Backup contains 0 records"
    echo "This is OK if you have no data yet, but unexpected if you've been using Hamilton UI"
    read -p "Continue anyway? (yes/no): " CONTINUE
    if [ "$CONTINUE" != "yes" ]; then
        echo "Aborted. Backup saved at: $BACKUP_FILE"
        exit 0
    fi
fi

echo ""
echo "================================================================"
echo "Step 2: Removing PostgreSQL 12 data"
echo "================================================================"
echo ""
echo "⚠️  WARNING: About to delete PostgreSQL 12 data volume"
echo "   Backup: $BACKUP_FILE ($RECORD_COUNT records)"
echo ""
read -p "Type 'DELETE' to confirm: " CONFIRM_DELETE

if [ "$CONFIRM_DELETE" != "DELETE" ]; then
    echo "Aborted. Your backup is saved at: $BACKUP_FILE"
    exit 0
fi

echo ""
echo "Stopping containers..."
$DOCKER_COMPOSE down

echo "Removing PostgreSQL 12 volume..."
if docker volume rm ui_postgres_data; then
    echo "✓ Volume removed"
else
    echo "Error: Could not remove volume"
    echo "It may not exist or be in use by another container"
    docker volume ls | grep postgres
    exit 1
fi

echo ""
echo "================================================================"
echo "Step 3: Starting PostgreSQL 18"
echo "================================================================"
echo ""

if [ ! -f "./run.sh" ]; then
    echo "Error: ./run.sh not found"
    echo "Run this script from the ui/ directory"
    exit 1
fi

echo "Building and starting containers..."
echo "(This may take a few minutes on first build)"
echo ""

if ! ./run.sh --build; then
    echo ""
    echo "Error: Failed to start containers"
    echo "Your backup is safe at: $BACKUP_FILE"
    echo ""
    echo "To retry manually:"
    echo "  1. Fix any Docker issues"
    echo "  2. Run: ./run.sh --build"
    echo "  3. Run: ./restore_hamilton_data.sh $BACKUP_FILE"
    exit 1
fi

# Wait for backend to be ready
echo ""
echo "Waiting for backend to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

until $DOCKER_COMPOSE exec -T backend python manage.py migrate --check > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "Error: Backend not ready after $MAX_RETRIES attempts"
        echo "Your backup is safe at: $BACKUP_FILE"
        echo ""
        echo "To restore manually:"
        echo "  1. Wait for containers to be healthy: $DOCKER_COMPOSE ps"
        echo "  2. Run: ./restore_hamilton_data.sh $BACKUP_FILE"
        exit 1
    fi
    echo "  Waiting... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

echo "✓ Backend ready"

# Check new PostgreSQL version
NEW_PG_VERSION=$($DOCKER_COMPOSE exec -T db psql -U hamilton -d hamilton -At -c "SHOW server_version;" | cut -d. -f1)
echo "✓ PostgreSQL $NEW_PG_VERSION running"

echo ""
echo "================================================================"
echo "Step 4: Restoring Hamilton data"
echo "================================================================"
echo ""

# Copy backup into backend container so loaddata can access it
echo "Copying backup into container..."
$DOCKER_COMPOSE cp "$BACKUP_FILE" backend:/tmp/restore.json

# Use the restore script
if ! $DOCKER_COMPOSE exec -T backend bash -c "cd /code && python manage.py loaddata /tmp/restore.json"; then
    echo ""
    echo "Error: Data restore failed"
    echo "Your backup is safe at: $BACKUP_FILE"
    echo ""
    echo "To retry manually:"
    echo "  ./restore_hamilton_data.sh $BACKUP_FILE"
    exit 1
fi

echo "✓ Data restored"

# Verify
echo ""
echo "Verifying migration..."
POST_COUNTS=$($DOCKER_COMPOSE exec -T backend python manage.py shell <<'PYTHON'
from trackingserver_base.models import Project
from trackingserver_run_tracking.models import DAGRun

print(f"{Project.objects.count()},{DAGRun.objects.count()}")
PYTHON
)

IFS=',' read -r PROJECTS RUNS <<< "$POST_COUNTS"

echo "  Projects: $PROJECTS"
echo "  Runs: $RUNS"

echo ""
echo "================================================================"
echo "✅ Migration Complete!"
echo "================================================================"
echo ""
echo "Your Hamilton UI has been upgraded from PostgreSQL $PG_VERSION to $NEW_PG_VERSION"
echo ""
echo "Next steps:"
echo "  1. Navigate to http://localhost:8242"
echo "  2. Verify your projects and runs appear"
echo "  3. If everything looks good, delete the backup:"
echo "     rm $BACKUP_FILE"
echo ""
echo "If you encounter issues:"
echo "  - Backup file: $BACKUP_FILE"
echo "  - Check logs: $DOCKER_COMPOSE logs"
echo "  - Get help: https://github.com/apache/hamilton/issues"
