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

# Fully self-contained verification of apache-hamilton-ui.
# Downloads from SVN (or uses local artifacts), verifies signatures,
# checks licenses, builds from source, and runs functional tests.
#
# Usage:
#   ./verify_ui.sh <version> <rc>                    # download from SVN
#   ./verify_ui.sh <version> <rc> <artifacts_dir>    # use local artifacts
#   ./verify_ui.sh 0.0.18 0
#   ./verify_ui.sh 0.0.18 0 ./ui-rc0

set -euo pipefail

VERSION="${1:-}"
RC="${2:-}"
ARTIFACTS_DIR="${3:-}"

if [ -z "$VERSION" ] || [ -z "$RC" ]; then
    echo "Usage: $0 <version> <rc> [artifacts_dir]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE="apache-hamilton-ui"
SRC_TAR="${PACKAGE}-${VERSION}-incubating-src.tar.gz"
WHEEL="apache_hamilton_ui-${VERSION}-py3-none-any.whl"

echo "=== Verifying ${PACKAGE} ${VERSION}-RC${RC} ==="

# --- Step 1: Get artifacts ---
if [ -z "$ARTIFACTS_DIR" ]; then
    ARTIFACTS_DIR="/tmp/verify-ui-artifacts-$$"
    echo "Downloading from SVN..."
    svn export -q "https://dist.apache.org/repos/dist/dev/incubator/hamilton/${PACKAGE}/${VERSION}-RC${RC}/" "$ARTIFACTS_DIR"
fi

echo "Artifacts: $ARTIFACTS_DIR"
ls "$ARTIFACTS_DIR"/*.tar.gz "$ARTIFACTS_DIR"/*.whl 2>/dev/null || { echo "ERROR: No artifacts found"; exit 1; }

# --- Step 2: GPG signatures ---
echo ""
echo "--- Verifying GPG signatures ---"
curl -sO https://downloads.apache.org/incubator/hamilton/KEYS
gpg --import KEYS 2>/dev/null || true

for artifact in "$ARTIFACTS_DIR"/*.tar.gz "$ARTIFACTS_DIR"/*.whl; do
    [ -f "$artifact" ] || continue
    if gpg --verify "${artifact}.asc" "$artifact" 2>&1 | grep -q "Good signature"; then
        echo "  ✓ GPG OK: $(basename "$artifact")"
    else
        echo "  ✗ GPG FAILED: $(basename "$artifact")"
        exit 1
    fi
done

# --- Step 3: SHA512 checksums ---
echo ""
echo "--- Verifying SHA512 checksums ---"
for artifact in "$ARTIFACTS_DIR"/*.tar.gz "$ARTIFACTS_DIR"/*.whl; do
    [ -f "$artifact" ] || continue
    expected=$(cat "${artifact}.sha512")
    actual=$(shasum -a 512 "$artifact" | awk '{print $1}')
    if [ "$expected" = "$actual" ]; then
        echo "  ✓ SHA512 OK: $(basename "$artifact")"
    else
        echo "  ✗ SHA512 MISMATCH: $(basename "$artifact")"
        exit 1
    fi
done

# --- Step 4: Apache RAT license check ---
echo ""
echo "--- Checking license headers (Apache RAT) ---"
RAT_JAR="${SCRIPT_DIR}/../apache-rat-0.15.jar"
if [ ! -f "$RAT_JAR" ]; then
    RAT_JAR="/tmp/apache-rat-0.15.jar"
    [ -f "$RAT_JAR" ] || curl -sO -o "$RAT_JAR" https://repo1.maven.org/maven2/org/apache/rat/apache-rat/0.15/apache-rat-0.15.jar
fi
RAT_EXCLUDES="${SCRIPT_DIR}/../../.rat-excludes"

extract_dir="/tmp/rat-ui-$$"
mkdir -p "$extract_dir"
tar xzf "$ARTIFACTS_DIR/$SRC_TAR" -C "$extract_dir"
unknown=$(java -jar "$RAT_JAR" -E "$RAT_EXCLUDES" -d "$extract_dir" 2>&1 | grep -c "!?????" || true)
if [ "$unknown" -eq 0 ]; then
    echo "  ✓ All files have approved licenses"
else
    echo "  ✗ ${unknown} file(s) missing license headers"
    java -jar "$RAT_JAR" -E "$RAT_EXCLUDES" -d "$extract_dir" 2>&1 | grep "!?????"
    rm -rf "$extract_dir"
    exit 1
fi
rm -rf "$extract_dir"

# --- Step 5: Build from source ---
echo ""
echo "--- Building from source ---"
build_dir="/tmp/build-ui-$$"
mkdir -p "$build_dir"
tar xzf "$ARTIFACTS_DIR/$SRC_TAR" -C "$build_dir"
src_dir=$(ls -d ${build_dir}/*/ | head -1)

# Note: The UI source tarball does not include compiled frontend assets.
# The release script builds the frontend (npm run build) before flit build.
# Here we verify the backend builds correctly; the wheel from SVN includes
# the pre-compiled frontend and is what's tested in step 6.
if (cd "$src_dir" && uvx flit build --no-use-vcs) 2>&1 | grep -q "Built wheel"; then
    echo "  ✓ Built from source successfully (backend only)"
else
    echo "  ✗ Build from source failed"
    rm -rf "$build_dir"
    exit 1
fi
rm -rf "$build_dir"

# --- Step 6: Functional verification ---
echo ""
echo "--- Functional verification ---"
VENV_DIR="/tmp/verify-ui-func-$$"
HAMILTON_BASE_DIR="/tmp/verify-ui-data-$$"
PORT=8241

uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"
cd /tmp  # prevent '' in sys.path from resolving local hamilton checkout

uv pip install -q "$ARTIFACTS_DIR/$WHEEL" apache-hamilton packaging

python -c "import importlib.metadata; assert importlib.metadata.version('apache-hamilton-ui') == '${VERSION}'"
echo "  ✓ Version correct"

# Start server in mini mode
mkdir -p "$HAMILTON_BASE_DIR/blobs" "$HAMILTON_BASE_DIR/db"
HAMILTON_BASE_DIR="$HAMILTON_BASE_DIR" python -m hamilton.cli ui --settings-file mini --no-open --port $PORT > /dev/null 2>&1 &
UI_PID=$!

# Wait for server to be ready
echo "  Waiting for server..."
for i in $(seq 1 15); do
    if python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/api/ping')" 2>/dev/null; then
        break
    fi
    sleep 2
done

# Health check
health=$(python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:${PORT}/api/ping').read().decode())" 2>/dev/null || echo "FAIL")
if [ "$health" = "ok" ]; then
    echo "  ✓ Health check OK"
else
    echo "  ✗ Health check FAILED (got: $health)"
    kill $UI_PID 2>/dev/null; wait $UI_PID 2>/dev/null || true
    deactivate; rm -rf "$VENV_DIR" "$HAMILTON_BASE_DIR"
    exit 1
fi

# Frontend check
python -c "
import importlib.util, sys, urllib.request, urllib.error
from pathlib import Path

spec = importlib.util.find_spec('hamilton_ui')
pkg_dir = Path(spec.origin).parent
index_html = pkg_dir / 'build' / 'index.html'
if not index_html.exists():
    print(f'  ✗ Frontend not bundled in wheel (missing {index_html})', file=sys.stderr)
    sys.exit(1)

try:
    resp = urllib.request.urlopen('http://localhost:${PORT}/')
    html = resp.read().decode()
    assert '<div id=\"root\"' in html or '<html' in html.lower(), 'No HTML served'
except urllib.error.HTTPError as e:
    print(f'  ✗ GET / returned HTTP {e.code} — server error despite bundled frontend', file=sys.stderr)
    sys.exit(1)
"
echo "  ✓ Frontend serves HTML"

kill $UI_PID 2>/dev/null; wait $UI_PID 2>/dev/null || true
deactivate
rm -rf "$VENV_DIR" "$HAMILTON_BASE_DIR"

echo ""
echo "=== ${PACKAGE} ${VERSION}-RC${RC}: ALL CHECKS PASSED ==="
