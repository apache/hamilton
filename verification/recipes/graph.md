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
kind: feature
covers: hamilton/graph.py, hamilton/graph_types.py, hamilton/graph_utils.py, hamilton/node.py, hamilton/htypes.py, hamilton/models.py, tests/test_graph.py, tests/test_graph_types.py, tests/test_node.py, tests/test_type_utils.py
---
# Functions become a graph

Hamilton turns a module's functions into nodes and their parameters into edges, checks that the types on each edge fit, and lets a user inspect the resulting graph.

## How a user reaches it

- Any driver build, which assembles the graph from the modules it is given.
- `dr.list_available_variables()` and `dr.graph` for the graph's public view (`graph_types.HamiltonGraph`).
- Type hints on nodes, including `htypes.column`, `Parallelizable`, and `Collect`, which decide what may connect.

## Scenarios

### tests
Run: `command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH (CI installs graphviz)' >&2; exit 3; }; uv sync --group test && uv run pytest tests/test_graph.py tests/test_graph_types.py tests/test_node.py tests/test_type_utils.py || exit $(($? == 3 ? 1 : $?))`
Proves: graph assembly, node creation, type matching on edges, and the public graph types pass their tests.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- Graph rendering needs Graphviz's `dot` on PATH; without it the scenario exits 3.
