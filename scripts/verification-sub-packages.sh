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

# =============================================================================
# Apache Hamilton Sub-Package Release Candidate Validation Script
#
# Validates sub-package release candidates by:
#   1. Downloading artifacts from Apache SVN
#   2. Verifying GPG signatures and SHA512 checksums
#   3. Checking Apache license headers with Apache RAT
#   4. Building from source tarballs
#   5. Running functional verification for each package
#
# Prerequisites: svn, gpg, java (for RAT), uv, curl, flit
#
# Usage:
#   ./verification-sub-packages.sh <rc>
#   ./verification-sub-packages.sh 0           # validate RC0
# =============================================================================

set -euo pipefail

RC="${1:-0}"

SDK_VERSION="0.9.0"
UI_VERSION="0.0.18"
LSP_VERSION="0.2.0"
CONTRIB_VERSION="0.0.9"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK_DIR="hamilton-subpkgs-rc${RC}-validation"
SVN_BASE="https://dist.apache.org/repos/dist/dev/incubator/hamilton"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

section() { echo -e "\n${GREEN}==============================================================================${NC}"; echo -e "  $1"; echo -e "${GREEN}==============================================================================${NC}\n"; }

declare -A PKG_VERSIONS=(
    ["sdk"]="$SDK_VERSION"
    ["ui"]="$UI_VERSION"
    ["lsp"]="$LSP_VERSION"
    ["contrib"]="$CONTRIB_VERSION"
)

declare -A PKG_NAMES=(
    ["sdk"]="apache-hamilton-sdk"
    ["ui"]="apache-hamilton-ui"
    ["lsp"]="apache-hamilton-lsp"
    ["contrib"]="apache-hamilton-contrib"
)

# =============================================================================
section "Step 1: Downloading Artifacts from SVN"
# =============================================================================

if [ -d "$WORK_DIR" ]; then
    rm -rf "$WORK_DIR"
fi
mkdir -p "$WORK_DIR"

for key in sdk ui lsp contrib; do
    name="${PKG_NAMES[$key]}"
    version="${PKG_VERSIONS[$key]}"
    echo "Downloading ${name} ${version}-RC${RC}..."
    svn export -q "${SVN_BASE}/${name}/${version}-RC${RC}/" "${WORK_DIR}/${key}/"
done

# =============================================================================
section "Step 2: Verifying GPG Signatures and SHA512 Checksums"
# =============================================================================

curl -sO https://downloads.apache.org/incubator/hamilton/KEYS
gpg --import KEYS 2>&1 | tail -1

for key in sdk ui lsp contrib; do
    echo ""
    echo "--- ${PKG_NAMES[$key]} ---"
    for artifact in ${WORK_DIR}/${key}/*.tar.gz ${WORK_DIR}/${key}/*.whl; do
        [ -f "$artifact" ] || continue
        gpg --verify "${artifact}.asc" "$artifact" 2>&1 | grep -E "Good signature|BAD"
        expected=$(cat "${artifact}.sha512")
        actual=$(shasum -a 512 "$artifact" | awk '{print $1}')
        if [ "$expected" = "$actual" ]; then
            echo "  ✓ SHA512 OK: $(basename "$artifact")"
        else
            echo "  ✗ SHA512 MISMATCH: $(basename "$artifact")"
            exit 1
        fi
    done
done

# =============================================================================
section "Step 3: Checking License Headers (Apache RAT)"
# =============================================================================

if [ ! -f "apache-rat-0.15.jar" ]; then
    curl -sO https://repo1.maven.org/maven2/org/apache/rat/apache-rat/0.15/apache-rat-0.15.jar
fi

for key in sdk ui lsp contrib; do
    src_tar=$(ls ${WORK_DIR}/${key}/*-src.tar.gz 2>/dev/null | head -1)
    echo "--- ${PKG_NAMES[$key]} ---"
    extract_dir="/tmp/rat-$$-${key}"
    mkdir -p "$extract_dir"
    tar xzf "$src_tar" -C "$extract_dir"
    unknown=$(java -jar apache-rat-0.15.jar -d "$extract_dir" 2>&1 | grep -c "!?????" || true)
    if [ "$unknown" -eq 0 ]; then
        echo "  ✓ All files have approved licenses"
    else
        echo "  ✗ ${unknown} file(s) missing license headers"
        java -jar apache-rat-0.15.jar -d "$extract_dir" 2>&1 | grep "!?????"
        exit 1
    fi
    rm -rf "$extract_dir"
done

# =============================================================================
section "Step 4: Building from Source"
# =============================================================================

for key in sdk ui lsp contrib; do
    src_tar=$(ls ${WORK_DIR}/${key}/*-src.tar.gz 2>/dev/null | head -1)
    echo "--- ${PKG_NAMES[$key]} ---"
    extract_dir="/tmp/build-$$-${key}"
    mkdir -p "$extract_dir"
    tar xzf "$src_tar" -C "$extract_dir"
    build_dir=$(ls -d ${extract_dir}/*/ | head -1)
    if (cd "$build_dir" && flit build --no-use-vcs) 2>&1 | grep -q "Built wheel"; then
        echo "  ✓ Built from source"
    else
        echo "  ✗ Build failed"
        exit 1
    fi
    rm -rf "$extract_dir"
done

# =============================================================================
section "Step 5: Functional Verification"
# =============================================================================

echo "Running individual package verification scripts..."
echo ""

bash "${SCRIPT_DIR}/verify-sub-packages/verify_sdk.sh" "$SDK_VERSION" "${WORK_DIR}/sdk"
echo ""
bash "${SCRIPT_DIR}/verify-sub-packages/verify_ui.sh" "$UI_VERSION" "${WORK_DIR}/ui"
echo ""
bash "${SCRIPT_DIR}/verify-sub-packages/verify_lsp.sh" "$LSP_VERSION" "${WORK_DIR}/lsp"
echo ""
bash "${SCRIPT_DIR}/verify-sub-packages/verify_contrib.sh" "$CONTRIB_VERSION" "${WORK_DIR}/contrib"

# =============================================================================
section "All Checks Passed!"
# =============================================================================

echo -e "${GREEN}All sub-package RCs validated successfully.${NC}"
echo ""
echo "Packages verified:"
echo "  apache-hamilton-sdk     ${SDK_VERSION}-RC${RC}"
echo "  apache-hamilton-ui      ${UI_VERSION}-RC${RC}"
echo "  apache-hamilton-lsp     ${LSP_VERSION}-RC${RC}"
echo "  apache-hamilton-contrib ${CONTRIB_VERSION}-RC${RC}"
