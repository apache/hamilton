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

# Verify apache-hamilton-sdk installs and works.
#
# Usage:
#   ./verify_sdk.sh [version]
#   ./verify_sdk.sh 0.9.0

set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VENV_DIR="/tmp/verify-sdk-$$"
echo "=== Verifying apache-hamilton-sdk ${VERSION} ==="

# Create isolated environment
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"

# Install
echo "Installing..."
uv pip install -q apache-hamilton "apache-hamilton-sdk==${VERSION}"

# Version check
echo "Checking version..."
python -c "import hamilton_sdk; assert hamilton_sdk.__version__ == tuple(int(x) for x in '${VERSION}'.split('.')), f'Got {hamilton_sdk.__version__}'; print(f'  Version: {hamilton_sdk.__version__}')"

# Import check
echo "Checking imports..."
python -c "
from hamilton_sdk.adapters import HamiltonTracker
from hamilton_sdk.tracking import runs
print('  Imports: OK')
"

# CLI check
echo "Checking CLI..."
python -m hamilton_sdk.cli.cli --help > /dev/null
echo "  CLI: OK"

# Cleanup
deactivate
rm -rf "$VENV_DIR"

echo "=== apache-hamilton-sdk ${VERSION}: PASSED ==="
