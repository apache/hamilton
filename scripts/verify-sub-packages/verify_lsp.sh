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

# Verify apache-hamilton-lsp installs and responds to LSP initialize.
#
# Usage:
#   ./verify_lsp.sh [version]
#   ./verify_lsp.sh 0.2.0

set -euo pipefail

VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

VENV_DIR="/tmp/verify-lsp-$$"
echo "=== Verifying apache-hamilton-lsp ${VERSION} ==="

# Create isolated environment
uv venv "$VENV_DIR" --python 3.12 -q
source "$VENV_DIR/bin/activate"

# Install
echo "Installing..."
uv pip install -q "apache-hamilton[visualization]" "apache-hamilton-lsp==${VERSION}"

# Version check
echo "Checking version..."
python -c "from hamilton_lsp import __version__; assert __version__ == '${VERSION}', f'Got {__version__}'; print(f'  Version: {__version__}')"

# LSP initialize test
echo "Checking LSP responds to initialize..."
python -c "
import subprocess, json, os

proc = subprocess.Popen(
    ['hamilton-lsp'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

request = json.dumps({
    'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
    'params': {'capabilities': {}, 'rootUri': 'file:///tmp', 'processId': os.getpid()}
})
msg = f'Content-Length: {len(request)}\r\n\r\n{request}'
proc.stdin.write(msg.encode())
proc.stdin.flush()

# Read response headers until blank line
while True:
    line = proc.stdout.readline()
    if line.strip() == b'':
        break
    if b'Content-Length' in line:
        content_length = int(line.split(b':')[1].strip())

body = proc.stdout.read(content_length)
proc.kill()
proc.wait()

resp = json.loads(body)
caps = resp.get('result', {}).get('capabilities', {})
assert 'textDocumentSync' in caps, f'Missing capabilities, got: {list(caps.keys())}'
print(f'  Capabilities: {list(caps.keys())}')
print('  LSP initialize: OK')
"

# Cleanup
deactivate
rm -rf "$VENV_DIR"

echo "=== apache-hamilton-lsp ${VERSION}: PASSED ==="
