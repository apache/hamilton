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
covers: hamilton/execution, tests/execution, tests/test_parallel_graceful.py
---
# Run nodes in parallel

A user enables dynamic execution so `Parallelizable` and `Collect` nodes fan out over tasks that local or remote executors run.

## How a user reaches it

- `driver.Builder().enable_dynamic_execution(allow_experimental_mode=True)` with `.with_local_executor(...)` and `.with_remote_executor(...)`.
- `executors.SynchronousLocalTaskExecutor`, `MultiThreadingExecutor`, and `MultiProcessingExecutor`.
- `Parallelizable[...]` and `Collect[...]` return and parameter types.

## Scenarios

### tests
Run: `uv sync --group test && uv run pytest tests/execution tests/test_parallel_graceful.py || exit $(($? == 3 ? 1 : $?))`
Proves: node grouping into tasks, the executors, and graceful failure in parallel branches pass their tests.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- The ray and dask executors are checked by the `h_ray` and `h_dask` recipes, not here.
