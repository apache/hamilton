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

# restore_hamilton_data.sh - Import Hamilton UI data using Django's loaddata

set -euo pipefail

BACKUP_FILE="${1:-}"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.json>"
    echo ""
    echo "Available backups:"
    ls -lh hamilton_data_*.json 2>/dev/null || echo "  (none found)"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Hamilton UI Data Restore"
echo "========================"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""

# Validate JSON
echo "Validating backup file..."
if ! python3 -m json.tool "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "Error: Backup file contains invalid JSON"
    exit 1
fi

RECORD_COUNT=$(python3 -c "import json; print(len(json.load(open('$BACKUP_FILE'))))")
echo "✓ Found $RECORD_COUNT records"
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
    echo "Start containers first: ./run.sh"
    exit 1
fi

# Check if database is ready
echo "Checking database connection..."
if ! $DOCKER_COMPOSE exec -T backend python manage.py migrate --check > /dev/null 2>&1; then
    echo "Error: Database is not ready or migrations need to run"
    echo "This is normal for a fresh installation."
    echo ""
    echo "Running migrations..."
    if ! $DOCKER_COMPOSE exec -T backend python manage.py migrate; then
        echo "Error: Migrations failed"
        exit 1
    fi
    echo "✓ Migrations complete"
fi
echo "✓ Database ready"
echo ""

# Check if there's existing data
EXISTING_PROJECTS=$($DOCKER_COMPOSE exec -T backend python manage.py shell -c "from trackingserver_base.models import *; print(Project.objects.count())" 2>/dev/null || echo "0")

if [ "$EXISTING_PROJECTS" != "0" ]; then
    echo "⚠️  WARNING: Database already contains $EXISTING_PROJECTS projects"
    echo ""
    echo "Restoring will ADD to existing data (not replace it)."
    echo "This may cause conflicts if the same data exists."
    echo ""
    read -p "Continue with restore? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# Create a pre-restore snapshot of record counts
echo "Creating pre-restore snapshot..."
PRE_RESTORE_COUNTS=$($DOCKER_COMPOSE exec -T backend python manage.py shell <<'PYTHON'
from trackingserver_base.models import Project
from trackingserver_projects.models import ProjectVersion
from trackingserver_run_tracking.models import DAGRun, DAGTemplate

print(f"{Project.objects.count()},{ProjectVersion.objects.count()},{DAGRun.objects.count()},{DAGTemplate.objects.count()}")
PYTHON
)

IFS=',' read -r PRE_PROJECTS PRE_VERSIONS PRE_RUNS PRE_TEMPLATES <<< "$PRE_RESTORE_COUNTS"

echo "  Projects: $PRE_PROJECTS"
echo "  Versions: $PRE_VERSIONS"
echo "  Runs: $PRE_RUNS"
echo "  Templates: $PRE_TEMPLATES"
echo ""

# Restore data using Django's loaddata
echo "Restoring data..."
RESTORE_LOG="/tmp/hamilton_restore_$(date +%Y%m%d_%H%M%S).log"

if ! $DOCKER_COMPOSE exec -T backend python manage.py loaddata "$BACKUP_FILE" > "$RESTORE_LOG" 2>&1; then
    echo "Error: Restore failed"
    echo ""
    echo "Log file: $RESTORE_LOG"
    echo ""
    echo "Last 20 lines of error:"
    tail -20 "$RESTORE_LOG"
    exit 1
fi

echo "✓ Data loaded"
echo ""

# Verify restore by comparing counts
echo "Verifying restore..."
POST_RESTORE_COUNTS=$($DOCKER_COMPOSE exec -T backend python manage.py shell <<'PYTHON'
from trackingserver_base.models import Project
from trackingserver_projects.models import ProjectVersion
from trackingserver_run_tracking.models import DAGRun, DAGTemplate

print(f"{Project.objects.count()},{ProjectVersion.objects.count()},{DAGRun.objects.count()},{DAGTemplate.objects.count()}")
PYTHON
)

IFS=',' read -r POST_PROJECTS POST_VERSIONS POST_RUNS POST_TEMPLATES <<< "$POST_RESTORE_COUNTS"

ADDED_PROJECTS=$((POST_PROJECTS - PRE_PROJECTS))
ADDED_VERSIONS=$((POST_VERSIONS - PRE_VERSIONS))
ADDED_RUNS=$((POST_RUNS - PRE_RUNS))
ADDED_TEMPLATES=$((POST_TEMPLATES - PRE_TEMPLATES))

echo "Records added:"
echo "  Projects: $ADDED_PROJECTS (total: $POST_PROJECTS)"
echo "  Versions: $ADDED_VERSIONS (total: $POST_VERSIONS)"
echo "  Runs: $ADDED_RUNS (total: $POST_RUNS)"
echo "  Templates: $ADDED_TEMPLATES (total: $POST_TEMPLATES)"
echo ""

# Sanity check - if we expected to add data but nothing changed
EXPECTED_RECORDS=$(python3 -c "
import json
data = json.load(open('$BACKUP_FILE'))
models = [item['model'] for item in data]
print(len([m for m in models if 'project' in m or 'dagrun' in m or 'dagtemplate' in m]))
")

if [ "$EXPECTED_RECORDS" -gt 0 ] && [ "$ADDED_PROJECTS" -eq 0 ] && [ "$ADDED_RUNS" -eq 0 ]; then
    echo "⚠️  Warning: Backup contained records but none were added"
    echo "   This could mean:"
    echo "   - Records already exist (duplicates skipped)"
    echo "   - Backup is from a different schema version"
    echo "   - There was an error during restore"
    echo ""
    echo "   Check the restore log: $RESTORE_LOG"
    exit 1
fi

echo "✓ Restore complete!"
echo ""
echo "Next steps:"
echo "  1. Navigate to http://localhost:8242"
echo "  2. Verify your projects and runs appear"
echo "  3. Check that data looks correct"
echo ""
echo "If something looks wrong:"
echo "  - Check logs: $DOCKER_COMPOSE logs backend"
echo "  - Restore log: $RESTORE_LOG"
