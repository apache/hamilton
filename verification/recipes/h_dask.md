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
covers: hamilton/plugins/h_dask.py, hamilton/plugins/dask_extensions.py, plugin_tests/h_dask
---
# Scale out with dask

A user runs a dataflow on a dask cluster, node by node or task by task, and gets dask or pandas results back.

## How a user reaches it

- `h_dask.DaskGraphAdapter(client, ...)` as the driver's adapter.
- `h_dask.DaskExecutor(client=...)` as a remote executor with dynamic execution.
- `h_dask.DaskDataFrameResult` as a result builder.

## Scenarios

### dask
Run: `uv sync --group test --extra dask && uv run pytest plugin_tests/h_dask || exit $(($? == 3 ? 1 : $?))`
Proves: the dask graph adapter, result builder, and executor integration tests pass with the `dask` extra, as CI's *Test dask* step runs them.

## Gotchas

- Its scenario is the suite's `dask` scenario word for word; keep the two identical when CI's step changes.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- The tests start a local dask `Client`; nothing outside the machine is used.
