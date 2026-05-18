#!/usr/bin/env bash
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

# Verify apache-hamilton-ui installs, starts in mini mode, and accepts SDK data.
#
# Usage:
#   ./verify_ui.sh [version]
#   ./verify_ui.sh 0.0.18

set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VENV_DIR="/tmp/verify-ui-$$"
HAMILTON_BASE_DIR="/tmp/verify-hamilton-ui-$$"
PORT=8241
echo "=== Verifying apache-hamilton-ui ${VERSION} ==="

# Create isolated environment
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"

# Install
echo "Installing..."
uv pip install -q apache-hamilton "apache-hamilton-ui==${VERSION}"

# Version check
echo "Checking version..."
python -c "import importlib.metadata; v = importlib.metadata.version('apache-hamilton-ui'); assert v == '${VERSION}', f'Got {v}'; print(f'  Version: {v}')"

# Start server in mini mode
echo "Starting server in mini mode..."
mkdir -p "$HAMILTON_BASE_DIR/blobs" "$HAMILTON_BASE_DIR/db"
HAMILTON_BASE_DIR="$HAMILTON_BASE_DIR" python -m hamilton.cli ui --settings-file mini --no-open --port $PORT &
SERVER_PID=$!
sleep 5

# Health check
echo "Checking health endpoint..."
HEALTH=$(python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:${PORT}/api/ping').read().decode())")
if [ "$HEALTH" = "ok" ]; then
    echo "  Health check: OK"
else
    echo "  Health check: FAILED (got: $HEALTH)"
    kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null
    exit 1
fi

# Frontend check
echo "Checking frontend serves..."
python -c "
import urllib.request
resp = urllib.request.urlopen('http://localhost:${PORT}/')
html = resp.read().decode()
assert '<div id=\"root\"' in html or '<html' in html.lower(), 'No HTML served'
print('  Frontend: OK')
"

# Cleanup
kill $SERVER_PID 2>/dev/null; wait $SERVER_PID 2>/dev/null || true
deactivate
rm -rf "$VENV_DIR" "$HAMILTON_BASE_DIR"

echo "=== apache-hamilton-ui ${VERSION}: PASSED ==="
