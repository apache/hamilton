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
covers: hamilton/plugins/h_ray.py, plugin_tests/h_ray
---
# Scale out with ray

A user runs a dataflow's nodes or tasks as ray remote functions, with per-node ray options set by tags.

## How a user reaches it

- `h_ray.RayGraphAdapter(result_builder, ...)` as the driver's adapter.
- `h_ray.RayTaskExecutor(...)` as a remote executor with dynamic execution.
- `@ray_remote_options(...)` on a node, which sets the ray options its task runs with.

## Scenarios

### ray
Run: `uv run --no-sync python -c 'import sys; sys.exit(sys.version_info >= (3, 15))' || { echo 'the ray extra installs ray only on Python 3.14 or older, and CI skips it on newer: uv sync --python 3.14 first' >&2; exit 3; }; uv sync --group test --extra ray && RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run pytest plugin_tests/h_ray || exit $(($? == 3 ? 1 : $?))`
Proves: the ray graph adapter, task executor, and remote-option parsing tests pass with the `ray` extra, as CI's *Test ray* step runs them.

## Gotchas

- Its scenario is the suite's `ray` scenario word for word; keep the two identical when CI's step changes.
- CI runs the step only on the Pythons its `if:` names, where the `ray` extra installs ray; elsewhere the scenario exits 3 (unreachable), and its message names a Python it runs on.
- `RAY_ENABLE_UV_RUN_RUNTIME_ENV=0` stops ray from rebuilding the uv environment on its workers (ray-project/ray#53848); keep it.
- The tests start a local ray instance with `ray.init()`; nothing outside the machine is used.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
