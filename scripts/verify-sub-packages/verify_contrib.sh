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

# Verify apache-hamilton-contrib installs and dataflows are importable.
#
# Usage:
#   ./verify_contrib.sh [version]
#   ./verify_contrib.sh 0.0.9

set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VENV_DIR="/tmp/verify-contrib-$$"
echo "=== Verifying apache-hamilton-contrib ${VERSION} ==="

# Create isolated environment
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"

# Install
echo "Installing..."
uv pip install -q apache-hamilton "apache-hamilton-contrib==${VERSION}"

# Version check
echo "Checking version..."
python -c "import importlib.metadata; v = importlib.metadata.version('apache-hamilton-contrib'); assert v == '${VERSION}', f'Got {v}'; print(f'  Version: {v}')"

# Import check
echo "Checking imports..."
python -c "
from hamilton.contrib import version
print(f'  version.py VERSION: {version.VERSION}')
import hamilton.contrib.user
import hamilton.contrib.user.zilto
print('  Namespace imports: OK')
"

# Cleanup
deactivate
rm -rf "$VENV_DIR"

echo "=== apache-hamilton-contrib ${VERSION}: PASSED ==="
