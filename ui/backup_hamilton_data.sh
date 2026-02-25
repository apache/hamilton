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

# backup_hamilton_data.sh - Export Hamilton UI data using Django's dumpdata

set -euo pipefail

BACKUP_FILE="${1:-hamilton_data_$(date +%Y%m%d_%H%M%S).json}"

echo "Hamilton UI Data Backup"
echo "======================="
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
    echo "Error: Hamilton UI backend container is not running"
    echo "Start containers first: ./run.sh or ./dev.sh"
    exit 1
fi

# Check if database is ready
echo "Checking database connection..."
if ! $DOCKER_COMPOSE exec -T backend python manage.py migrate --check > /dev/null 2>&1; then
    echo "Error: Database is not ready or migrations are pending"
    echo "Run: $DOCKER_COMPOSE exec backend python manage.py migrate"
    exit 1
fi
echo "✓ Database connected"
echo ""

# List Hamilton UI Django apps (excluding Django system apps)
HAMILTON_APPS=(
    "trackingserver_base"
    "trackingserver_auth"
    "trackingserver_projects"
    "trackingserver_run_tracking"
    "trackingserver_template"
)

echo "Backing up Hamilton UI data..."
echo "Apps: ${HAMILTON_APPS[*]}"
echo ""

# Dump data using Django's dumpdata
# This is better than pg_dump because:
# - Handles foreign keys correctly
# - Portable JSON format (works across PostgreSQL versions)
# - Only dumps application data (not system tables)
# - Django handles restore ordering automatically
if ! $DOCKER_COMPOSE exec -T backend python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --indent 2 \
    "${HAMILTON_APPS[@]}" > "$BACKUP_FILE"; then
    echo "Error: Backup failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Validate backup file
if [ ! -s "$BACKUP_FILE" ]; then
    echo "Error: Backup file is empty"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Check if it's valid JSON
if ! python3 -m json.tool "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "Error: Backup file contains invalid JSON"
    exit 1
fi

# Count records
RECORD_COUNT=$(python3 -c "import json; print(len(json.load(open('$BACKUP_FILE'))))")
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "✓ Backup complete"
echo ""
echo "File: $BACKUP_FILE"
echo "Size: $FILE_SIZE"
echo "Records: $RECORD_COUNT"
echo ""

# Show breakdown by model
echo "Records by model:"
python3 -c "
import json
from collections import Counter

data = json.load(open('$BACKUP_FILE'))
models = Counter(item['model'] for item in data)

for model, count in sorted(models.items()):
    print(f'  {model}: {count}')
"

echo ""
echo "To restore this backup on a new system:"
echo "  1. Start Hamilton UI: ./run.sh"
echo "  2. Run: ./restore_hamilton_data.sh $BACKUP_FILE"
