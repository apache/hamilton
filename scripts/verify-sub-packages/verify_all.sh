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

# Verify all sub-packages install together and work.
#
# Usage:
#   ./verify_all.sh <hamilton_version> <sdk_version> <ui_version> <lsp_version> <contrib_version>
#   ./verify_all.sh 1.90.0 0.9.0 0.0.18 0.2.0 0.0.9

set -euo pipefail

if [ $# -ne 5 ]; then
    echo "Usage: $0 <hamilton_version> <sdk_version> <ui_version> <lsp_version> <contrib_version>"
    echo "Example: $0 1.90.0 0.9.0 0.0.18 0.2.0 0.0.9"
    exit 1
fi

HAMILTON_VERSION="$1"
SDK_VERSION="$2"
UI_VERSION="$3"
LSP_VERSION="$4"
CONTRIB_VERSION="$5"

VENV_DIR="/tmp/verify-all-$$"
echo "=== Verifying all sub-packages together ==="

# Create isolated environment
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"

# Install all
echo "Installing all packages..."
uv pip install -q \
    "apache-hamilton==${HAMILTON_VERSION}" \
    "apache-hamilton-sdk==${SDK_VERSION}" \
    "apache-hamilton-ui==${UI_VERSION}" \
    "apache-hamilton-lsp==${LSP_VERSION}" \
    "apache-hamilton-contrib==${CONTRIB_VERSION}"

# Verify all imports
echo "Checking imports..."
python -c "
import hamilton
import hamilton_sdk
import hamilton_ui
import hamilton_lsp
import importlib.metadata

print(f'  hamilton:        {hamilton.version.VERSION}')
print(f'  hamilton-sdk:    {hamilton_sdk.__version__}')
print(f'  hamilton-lsp:    {hamilton_lsp.__version__}')
print(f'  hamilton-contrib: {importlib.metadata.version(\"apache-hamilton-contrib\")}')
print('  All imports: OK')
"

# Cleanup
deactivate
rm -rf "$VENV_DIR"

echo "=== All sub-packages together: PASSED ==="
