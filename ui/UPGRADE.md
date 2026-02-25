<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Hamilton UI Upgrade Guide

This guide covers backward compatibility concerns and migration steps when upgrading Hamilton UI.

## Upgrading from PostgreSQL 12 to PostgreSQL 18

**Affected versions:** Upgrading to versions after commit `0da07178` (February 2026)

### What Changed

Hamilton UI Docker setup now uses **PostgreSQL 18** instead of PostgreSQL 12 to support Django 6.0.2+, which requires PostgreSQL 13 or later.

**Important:** PostgreSQL 18 Docker images use a new data directory structure. The volume mount point has changed from `/var/lib/postgresql/data` to `/var/lib/postgresql`. This allows PostgreSQL to store data in version-specific subdirectories (e.g., `/var/lib/postgresql/18/data`) and enables easier future upgrades using `pg_upgrade --link`.

**Why this matters:** You cannot simply change the image tag from `postgres:12` to `postgres:18` without migrating your data. The old volume will be incompatible with the new structure.

### Do I Need to Migrate?

**You need to migrate if ALL of the following are true:**
1. You have been using Hamilton UI with Docker (`./run.sh` or `./dev.sh`)
2. You have existing project data, runs, or artifacts you want to keep
3. You are upgrading from a version that used PostgreSQL 12

**You do NOT need to migrate if:**
- This is a fresh installation
- You don't care about preserving existing data
- You're using the PyPI package (`hamilton ui`) which uses SQLite by default

### Migration Options

#### Option 1: Fresh Start (Recommended for Development)

If your data is not critical (development/testing), the simplest approach is to start fresh:

```bash
cd hamilton/ui

# Stop containers
./stop.sh

# Remove old PostgreSQL 12 data
docker volume rm ui_postgres_data

# Start with PostgreSQL 18
./run.sh --build
```

**⚠️ Warning:** This will delete all existing projects, runs, and artifacts.

#### Option 2: Migrate Your Data

If you need to preserve your data, follow these steps:

##### Step 1: Export data from PostgreSQL 12

While still using the old version:

```bash
cd hamilton/ui

# Ensure containers are running
docker compose up -d

# Export data
docker compose exec db pg_dump -U hamilton hamilton > hamilton_backup.sql

# Stop containers
docker compose down
```

##### Step 2: Upgrade to PostgreSQL 18

```bash
# Remove old PostgreSQL 12 volume
docker volume rm ui_postgres_data

# Pull latest code with PostgreSQL 18
git pull  # or checkout the latest version

# Start new containers
./run.sh --build
```

##### Step 3: Import data into PostgreSQL 18

```bash
# Wait for database to be ready
sleep 10

# Import data
docker compose exec -T db psql -U hamilton hamilton < hamilton_backup.sql

# Verify data
docker compose exec db psql -U hamilton hamilton -c "\dt"
```

##### Step 4: Verify Migration

Navigate to http://localhost:8242 and verify:
- Your projects exist
- Run history is preserved
- Artifacts are accessible

##### Troubleshooting

**Issue:** Import fails with "relation already exists"

The Hamilton UI automatically runs migrations on startup, which creates empty tables. Your import will skip those errors - this is normal.

**Issue:** Permission errors on import

```bash
# Grant permissions to hamilton user
docker compose exec db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hamilton;"
docker compose exec db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hamilton;"
```

**Issue:** Blob/artifact files missing

If you stored artifacts locally (not S3), you also need to copy the blob storage:

```bash
# Identify blob storage location (check docker-compose.yml)
docker compose exec backend ls /code/blobs

# If using local storage, copy blobs directory
cp -r old_blobs_directory new_blobs_directory
```

**Issue:** PostgreSQL 18 fails with "Error: in 18+, these Docker images are configured to store database data in a format which is compatible with pg_ctlcluster"

This error means you have old PostgreSQL data (from version 12 or 16) that's incompatible with PostgreSQL 18's new directory structure. The PostgreSQL 18 Docker image expects data in `/var/lib/postgresql` (not `/var/lib/postgresql/data`).

**Solution:** You must migrate your data using the migration scripts provided. Do not try to reuse the old volume:

```bash
# Remove the old volume (after backing up your data!)
docker compose down
docker volume rm ui_postgres_data

# Follow the migration guide above to export and import your data
./migrate_postgres_simple.sh
```

If you're upgrading from PostgreSQL 16 to 18 and encounter this error, the volume mount point has changed. You still need to follow the migration process even though both versions are modern.

#### Option 3: Use pg_upgrade (Advanced)

For minimal downtime migrations, you can use PostgreSQL's `pg_upgrade` tool. This is more complex and generally not recommended for Hamilton UI due to its development-focused nature.

See [PostgreSQL pg_upgrade documentation](https://www.postgresql.org/docs/current/pgupgrade.html) for details.

## Other Breaking Changes

### Python Version (Internal)

The Docker images now use **Python 3.12** instead of Python 3.8. This is transparent to users - no action needed.

**Why:** Python 3.8 reached end-of-life in October 2024. Python 3.12 provides better performance and security.

### Dependency Management (Internal)

The Docker backend now uses **uv** instead of pip for dependency management. This is transparent to users - no action needed.

**Why:** uv provides faster installs and reproducible builds via lock files.

### Django 6.0+ Requirements

Django 6.0.2+ requires PostgreSQL 13 or later, which is why we upgraded to PostgreSQL 18.

## Migration Script

For automated migration, you can use this script:

```bash
#!/bin/bash
# migrate_postgres.sh - Migrate Hamilton UI from PostgreSQL 12 to 18

set -e

BACKUP_FILE="hamilton_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "Hamilton UI PostgreSQL 12 → 18 Migration"
echo "========================================"
echo ""

# Check if old containers are running
if ! docker compose ps | grep -q "ui-db"; then
    echo "Error: Hamilton UI containers not running. Start them first with ./run.sh"
    exit 1
fi

# Backup
echo "Step 1: Backing up PostgreSQL 12 data..."
docker compose exec -T db pg_dump -U hamilton hamilton > "$BACKUP_FILE"
echo "✓ Backup saved to: $BACKUP_FILE"
echo ""

# Stop and remove
echo "Step 2: Stopping containers and removing old data..."
docker compose down
docker volume rm ui_postgres_data
echo "✓ Old data removed"
echo ""

# Start new
echo "Step 3: Starting PostgreSQL 18..."
./run.sh --build
sleep 15  # Wait for initialization
echo "✓ PostgreSQL 18 ready"
echo ""

# Restore
echo "Step 4: Restoring data..."
docker compose exec -T db psql -U hamilton hamilton < "$BACKUP_FILE" 2>&1 | grep -v "ERROR:.*already exists" || true
echo "✓ Data restored"
echo ""

# Fix permissions
echo "Step 5: Fixing permissions..."
docker compose exec -T db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO hamilton;" > /dev/null
docker compose exec -T db psql -U hamilton hamilton -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO hamilton;" > /dev/null
echo "✓ Permissions fixed"
echo ""

echo "Migration complete!"
echo "Navigate to http://localhost:8242 to verify your data."
```

Save as `migrate_postgres.sh`, make executable with `chmod +x migrate_postgres.sh`, and run with `./migrate_postgres.sh`.

## Getting Help

If you encounter issues during migration:

1. Check the [Hamilton UI documentation](https://hamilton.apache.org/concepts/ui)
2. Search or create an issue on [GitHub](https://github.com/apache/hamilton/issues)
3. Join our [Slack community](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g)

## Version Compatibility Matrix

| Hamilton UI Version | PostgreSQL Version | Python Version | Django Version |
|--------------------|--------------------|----------------|----------------|
| < 0.0.17 (2026-02) | 12 | 3.8 | 4.2 |
| ≥ 0.0.17 (2026-02) | 18 | 3.12 | 6.0.2 |

## FAQ

**Q: Can I continue using PostgreSQL 12?**

No. Django 6.0.2+ explicitly requires PostgreSQL 13 or later. You must upgrade to at least PostgreSQL 13 (we recommend 18 for the latest features and long-term support).

**Q: Will my PyPI installation be affected?**

No. The PyPI package (`apache-hamilton-ui`) uses SQLite by default for local development. This upgrade only affects Docker deployments.

**Q: Can I downgrade if something goes wrong?**

Yes, as long as you keep your backup file:

```bash
# Checkout old version
git checkout <old_commit_before_upgrade>

# Remove new volume
docker volume rm ui_postgres_data

# Start old version
./run.sh --build

# Restore from backup (if needed)
docker compose exec -T db psql -U hamilton hamilton < hamilton_backup.sql
```

**Q: Do I need to update my Hamilton SDK client code?**

No. The Hamilton SDK (`apache-hamilton-sdk`) is compatible with both old and new versions of the UI backend. No client code changes required.
