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

# Builds an sf-hamilton* redirect package. Each sf-hamilton*-redirect/build.sh runs this.
#
# Usage:
#   scripts/build_redirect.sh <redirect-dir> <version>

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "Usage: ${1:-sf-hamilton-redirect}/build.sh <version>"
    echo "<version> is the version of the package it redirects to, as its pyproject.toml declares it."
    exit 1
fi

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
REDIRECT_DIR="$(cd "$1" && pwd)"
VERSION="$2"
NAME="$(basename "${REDIRECT_DIR}" -redirect)"

echo "Building ${NAME} redirect package for version ${VERSION}..."

# Render pyproject.toml from the template and the package this one redirects to
python "${SCRIPTS_DIR}/render_redirect_pyproject.py" "${REDIRECT_DIR}" "${VERSION}"

# Clean previous build
rm -rf "${REDIRECT_DIR}/dist" "${REDIRECT_DIR}/build" "${REDIRECT_DIR}"/*.egg-info

# Build
cd "${REDIRECT_DIR}"
python -m build

# Validate
twine check dist/*

echo ""
echo "Build complete. Artifacts:"
ls -la dist/
echo ""
echo "To upload: twine upload ${REDIRECT_DIR}/dist/*"
