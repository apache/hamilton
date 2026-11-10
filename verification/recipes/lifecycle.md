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
covers: hamilton/lifecycle, tests/lifecycle
---
# Hook into a run

A user adds adapters that run code before and after graph, node, and task execution, or that change how a node runs.

## How a user reaches it

- `driver.Builder().with_adapters(...)`.
- Subclassing `hamilton.lifecycle` bases such as `NodeExecutionHook`, `GraphExecutionHook`, `TaskExecutionHook`, `NodeExecutionMethod`, and `ResultBuilder`.
- The adapters `hamilton.lifecycle.default` ships, such as `PrintLn`, `PDBDebugger`, and `CacheAdapter`.

## Scenarios

### tests
Run: `uv sync --group test && uv run pytest tests/lifecycle || exit $(($? == 3 ? 1 : $?))`
Proves: every lifecycle hook and method fires in order, and the default adapters behave, in node-based and task-based runs.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
