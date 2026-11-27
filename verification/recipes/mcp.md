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

---
kind: plugin
covers: hamilton/plugins/h_mcp, tests/plugins/test_h_mcp.py
---
# Hamilton MCP server

An AI assistant connected to Hamilton's Model Context Protocol (MCP) server lists capabilities, scaffolds, validates, visualizes, and executes dataflows.

## How a user reaches it

- The `hamilton-mcp` console script, after `pip install apache-hamilton[mcp]`.
- `python -m hamilton.plugins.h_mcp`.

## Scenarios

### mcp
Run: `uv sync --group test --extra mcp && uv run pytest tests/plugins/test_h_mcp.py || exit $(($? == 3 ? 1 : $?))`
Proves: the MCP server tests pass with the `mcp` extra, as CI's *Test MCP* step runs them.

## Gotchas

- Its scenario is the suite's `mcp` scenario word for word; keep the two identical when CI's step changes.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- Without the `mcp` extra the test file skips itself (`importorskip("fastmcp")`) and passes on nothing; the scenario's own sync installs it.
