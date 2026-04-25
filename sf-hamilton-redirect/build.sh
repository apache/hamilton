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

# Builds the sf-hamilton redirect package for a given version.
#
# Usage:
#   ./build.sh <version>
#   ./build.sh 1.90.0

set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.90.0"
    exit 1
fi

VERSION="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Building sf-hamilton redirect package for version ${VERSION}..."

# Stamp version into pyproject.toml from template
sed "s/VERSION/${VERSION}/g" "${SCRIPT_DIR}/pyproject.toml.template" > "${SCRIPT_DIR}/pyproject.toml"

# Clean previous build
rm -rf "${SCRIPT_DIR}/dist" "${SCRIPT_DIR}/build" "${SCRIPT_DIR}"/*.egg-info

# Build
cd "${SCRIPT_DIR}"
python -m build

# Validate
twine check dist/*

echo ""
echo "Build complete. Artifacts:"
ls -la dist/
echo ""
echo "To upload: twine upload dist/sf_hamilton-${VERSION}*"
