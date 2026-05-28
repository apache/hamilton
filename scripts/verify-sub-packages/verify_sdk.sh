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

# Fully self-contained verification of apache-hamilton-sdk.
# Downloads from SVN (or uses local artifacts), verifies signatures,
# checks licenses, builds from source, and runs functional tests.
#
# Usage:
#   ./verify_sdk.sh <version> <rc>                    # download from SVN
#   ./verify_sdk.sh <version> <rc> <artifacts_dir>    # use local artifacts
#   ./verify_sdk.sh 0.9.0 0
#   ./verify_sdk.sh 0.9.0 0 ./sdk-rc0

set -euo pipefail

VERSION="${1:-}"
RC="${2:-}"
ARTIFACTS_DIR="${3:-}"

if [ -z "$VERSION" ] || [ -z "$RC" ]; then
    echo "Usage: $0 <version> <rc> [artifacts_dir]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PACKAGE="apache-hamilton-sdk"
SRC_TAR="${PACKAGE}-${VERSION}-incubating-src.tar.gz"
WHEEL="apache_hamilton_sdk-${VERSION}-py3-none-any.whl"

echo "=== Verifying ${PACKAGE} ${VERSION}-RC${RC} ==="

# --- Step 1: Get artifacts ---
if [ -z "$ARTIFACTS_DIR" ]; then
    ARTIFACTS_DIR="/tmp/verify-sdk-artifacts-$$"
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

extract_dir="/tmp/rat-sdk-$$"
mkdir -p "$extract_dir"
tar xzf "$ARTIFACTS_DIR/$SRC_TAR" -C "$extract_dir"
unknown=$(java -jar "$RAT_JAR" -E "$RAT_EXCLUDES" -d "$extract_dir" 2>&1 | grep -c "!?????" || true)
if [ "$unknown" -eq 0 ]; then
    echo "  ✓ All files have approved licenses"
else
    echo "  ✗ ${unknown} file(s) missing license headers"
    java -jar "$RAT_JAR" -d "$extract_dir" 2>&1 | grep "!?????"
    rm -rf "$extract_dir"
    exit 1
fi
rm -rf "$extract_dir"

# --- Step 5: Build from source ---
echo ""
echo "--- Building from source ---"
build_dir="/tmp/build-sdk-$$"
mkdir -p "$build_dir"
tar xzf "$ARTIFACTS_DIR/$SRC_TAR" -C "$build_dir"
src_dir=$(ls -d ${build_dir}/*/ | head -1)
if (cd "$src_dir" && uvx flit build --no-use-vcs) 2>&1 | grep -q "Built wheel"; then
    echo "  ✓ Built from source successfully"
else
    echo "  ✗ Build from source failed"
    rm -rf "$build_dir"
    exit 1
fi
rm -rf "$build_dir"

# --- Step 6: Functional verification ---
echo ""
echo "--- Functional verification ---"
VENV_DIR="/tmp/verify-sdk-func-$$"
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"
cd /tmp  # prevent '' in sys.path from resolving local hamilton checkout

uv pip install -q "$ARTIFACTS_DIR/$WHEEL" apache-hamilton

python -c "import hamilton_sdk; assert hamilton_sdk.__version__ == tuple(int(x) for x in '${VERSION}'.split('.')), f'Got {hamilton_sdk.__version__}'"
echo "  ✓ Version correct"

python -c "from hamilton_sdk.adapters import HamiltonTracker; from hamilton_sdk.tracking import runs"
echo "  ✓ Imports OK"

python -m hamilton_sdk.cli.cli --help > /dev/null
echo "  ✓ CLI OK"

deactivate
rm -rf "$VENV_DIR"

echo ""
echo "=== ${PACKAGE} ${VERSION}-RC${RC}: ALL CHECKS PASSED ==="
