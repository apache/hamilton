<!--
     Licensed to the Apache Software Foundation (ASF) under one
     or more contributor license agreements.  See the NOTICE file
     distributed with this work for additional information
     regarding copyright ownership.  The ASF licenses this file
     to you under the Apache License, Version 2.0 (the
     "License"); you may not use this file except in compliance
     with the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing,
     software distributed under the License is distributed on an
     "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
     KIND, either express or implied.  See the License for the
     specific language governing permissions and limitations
     under the License.
-->

# Verifying Sub-Package Releases

This guide covers how to validate the `apache-hamilton-sdk`, `apache-hamilton-ui`,
`apache-hamilton-lsp`, and `apache-hamilton-contrib` packages before voting on a release.

For the core `apache-hamilton` package verification, see `scripts/verification-script.sh`.

## Quick Start

```bash
# Set the versions being released
export SDK_VERSION=0.9.0
export UI_VERSION=0.0.18
export LSP_VERSION=0.2.0
export CONTRIB_VERSION=0.0.9
export HAMILTON_VERSION=1.90.0
```

## apache-hamilton-sdk

### Install and verify version

```bash
uv venv /tmp/verify-sdk --python 3.12
source /tmp/verify-sdk/bin/activate
uv pip install apache-hamilton apache-hamilton-sdk==${SDK_VERSION}

python -c "import hamilton_sdk; print(hamilton_sdk.__version__)"
# Expected: (0, 9, 0)
```

### Run unit tests (from source)

```bash
cd ui/sdk
uv sync --group test
uv run pytest tests/ -q
```

### Acceptance test: SDK tracks a run to UI server

Prerequisite: UI server running with a project created (see apache-hamilton-ui
section below — run the "UI accepts data from SDK" test which creates a project
and executes the full flow).

```bash
cd examples/hamilton_ui
uv pip install -r requirements.txt
uv run python run.py --username voter --project-id 1
```

This exercises the full SDK → UI pipeline: DAG template registration,
node-level tracking, attribute collection, and run completion.

### Example to run

See `examples/hamilton_ui/` — the same example above.

---

## apache-hamilton-ui

### Install and verify

```bash
uv venv /tmp/verify-ui --python 3.12
source /tmp/verify-ui/bin/activate
uv pip install apache-hamilton-ui==${UI_VERSION}
```

### Start server in mini mode (SQLite, no PostgreSQL needed)

```bash
export HAMILTON_BASE_DIR=/tmp/verify-hamilton-ui
mkdir -p $HAMILTON_BASE_DIR/blobs $HAMILTON_BASE_DIR/db

# Start the UI (opens browser, creates project via UI)
hamilton ui
# Or without opening browser:
# hamilton ui --no-open --port 8241
```

### Health check

```bash
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8241/api/ping').read())"
# Expected: b'ok'
```

### Run build verification tests (from source)

```bash
cd ui/backend
uv run pytest tests/test_build.py -v
```

### Acceptance test: UI serves frontend

```bash
python -c "
import urllib.request
resp = urllib.request.urlopen('http://localhost:8241/')
html = resp.read().decode()
assert '<div id=\"root\"' in html, 'Expected React root element in HTML'
print('UI frontend served successfully')
"
```

### Acceptance test: UI accepts data from SDK

This is the key integration test — verifies the UI server can receive and
store DAG tracking data sent by the SDK.

```bash
# Install SDK in the same venv
uv pip install apache-hamilton apache-hamilton-sdk==${SDK_VERSION} pandas

# Step 1: Open the UI in your browser and create a project.
# The `hamilton ui` command opens http://localhost:8241 automatically.
# Create a project and note its ID (shown in the URL, e.g. /dashboard/project/1).

# Step 2: Run the hamilton_ui example against the server
cd examples/hamilton_ui
uv pip install -r requirements.txt
python run.py --username <your_username> --project-id <project_id>
# Expected: "Captured execution run. Results can be found at ..."

# Step 3: Verify in the UI
# Navigate to http://localhost:8241/dashboard/project/<id>/runs
# You should see the DAG run with node-level details, attributes, etc.
```

This exercises the full SDK → UI pipeline: DAG template registration,
node-level tracking, attribute collection, and run completion.

---

## apache-hamilton-lsp

### Install and verify version

```bash
uv venv /tmp/verify-lsp --python 3.12
source /tmp/verify-lsp/bin/activate
uv pip install "apache-hamilton[visualization]" apache-hamilton-lsp==${LSP_VERSION}

python -c "from hamilton_lsp import __version__; print(__version__)"
# Expected: 0.2.0
```

### Run unit tests (from source)

```bash
cd dev_tools/language_server
uv pip install -e . pytest
uv run pytest tests/ -v
```

### Acceptance test: LSP responds to initialize request

The LSP communicates over stdin/stdout using JSON-RPC. Send an initialize
request and verify it responds with server capabilities:

```bash
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
print(f'Capabilities: {list(caps.keys())}')
print('LSP responded to initialize request: PASSED')
"
```

---

## apache-hamilton-contrib

### Install and verify version

```bash
uv venv /tmp/verify-contrib --python 3.12
source /tmp/verify-contrib/bin/activate
uv pip install apache-hamilton apache-hamilton-contrib==${CONTRIB_VERSION}

python -c "import importlib.metadata; print(importlib.metadata.version('apache-hamilton-contrib'))"
# Expected: 0.0.9
```

### Verify dataflow imports work

```bash
python -c "
from hamilton.contrib.user.zilto import xgboost_optuna
from hamilton import driver
import inspect

# Verify module has Hamilton functions
funcs = [n for n, f in inspect.getmembers(xgboost_optuna, inspect.isfunction)
         if not n.startswith('_')]
print(f'xgboost_optuna has {len(funcs)} functions')
assert len(funcs) > 0
print('Contrib dataflow import: OK')
"
```

### Example to run

```bash
cd examples/contrib
uv pip install -r requirements.txt
uv run python run.py
```

This runs the `xgboost_optuna` contrib dataflow end-to-end (trains a model,
tunes hyperparameters, saves results).

---

## All packages together

Verify all 4 sub-packages install alongside core hamilton without conflicts:

```bash
uv venv /tmp/verify-all --python 3.12
source /tmp/verify-all/bin/activate
uv pip install apache-hamilton==${HAMILTON_VERSION} \
  apache-hamilton-sdk==${SDK_VERSION} \
  apache-hamilton-ui==${UI_VERSION} \
  apache-hamilton-lsp==${LSP_VERSION} \
  apache-hamilton-contrib==${CONTRIB_VERSION}

python -c "
import hamilton
import hamilton_sdk
import hamilton_ui
import hamilton_lsp
import importlib.metadata

print(f'hamilton:       {hamilton.version.VERSION}')
print(f'hamilton-sdk:   {hamilton_sdk.__version__}')
print(f'hamilton-lsp:   {hamilton_lsp.__version__}')
print(f'hamilton-contrib: {importlib.metadata.version(\"apache-hamilton-contrib\")}')
print('All packages coexist without conflicts')
"
```

## Extras chain verification

Verify the `apache-hamilton[sdk]` extra correctly pulls in `apache-hamilton-sdk`:

```bash
uv venv /tmp/verify-extras --python 3.12
source /tmp/verify-extras/bin/activate
uv pip install "apache-hamilton[sdk,lsp]"

python -c "
import hamilton_sdk
import hamilton_lsp
print('Extras resolution: OK')
"
```

## Redirect package verification (after upload)

Verify that old `sf-hamilton-*` package names redirect to the new names:

```bash
uv venv /tmp/verify-redirects --python 3.12
source /tmp/verify-redirects/bin/activate
uv pip install sf-hamilton-sdk sf-hamilton-ui sf-hamilton-lsp sf-hamilton-contrib

uv pip show apache-hamilton-sdk | grep Version
uv pip show apache-hamilton-ui | grep Version
uv pip show apache-hamilton-lsp | grep Version
uv pip show apache-hamilton-contrib | grep Version
```
