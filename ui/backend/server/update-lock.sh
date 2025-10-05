#!/bin/bash
# Update uv.lock and regenerate requirements-locked.txt
set -e

cd "$(dirname "$0")"

echo "Updating uv.lock..."
uv lock

echo "Exporting requirements-locked.txt..."
uv export --no-hashes --no-emit-package hamilton-ui-backend > requirements-locked.txt

echo "Done! Lock files updated."
