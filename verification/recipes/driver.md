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
covers: hamilton/driver.py, hamilton/async_driver.py, hamilton/base.py, hamilton/ad_hoc_utils.py, hamilton/common, hamilton/dev_utils, hamilton/version.py, tests/test_hamilton_driver.py, tests/test_async_driver.py, tests/test_end_to_end.py, tests/test_driver_export.py, tests/test_base.py, tests/test_ad_hoc_utils.py, tests/test_common.py, tests/test_dev_utils.py, tests/test_deprecation_schedules.py
---
# Build and run a dataflow

A user builds a driver from Python modules and config, executes or materializes the nodes they ask for, and gets results shaped by a result builder; the same works with `async` functions.

## How a user reaches it

- `driver.Builder().with_modules(...).with_config(...).build()`, then `dr.execute([...])` or `dr.materialize(...)`.
- The older `driver.Driver(config, *modules, adapter=...)` constructor.
- `async_driver.AsyncDriver` and `async_driver.Builder` for modules of `async def` nodes.
- `dr.display_all_functions()`, `dr.visualize_execution(...)`, and `dr.export_execution(...)` to see or export the graph.
- `ad_hoc_utils.create_temporary_module(...)` to build a module from functions in a notebook.

## Scenarios

### tests
Run: `command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH (CI installs graphviz)' >&2; exit 3; }; uv sync --group test && uv run pytest tests/test_hamilton_driver.py tests/test_async_driver.py tests/test_end_to_end.py tests/test_driver_export.py tests/test_base.py tests/test_ad_hoc_utils.py tests/test_common.py tests/test_dev_utils.py tests/test_deprecation_schedules.py || exit $(($? == 3 ? 1 : $?))`
Proves: the driver, async driver, result builders, graph export, and the helpers they share pass their tests. Hamilton's own deprecations follow the release `hamilton/version.py` names. They warn at the user's calling line through the warning filters and fail when that release reaches their removal.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- Graph rendering needs Graphviz's `dot` on PATH; without it the scenario exits 3.
- Deprecations made with `hamilton/dev_utils/deprecation.py` read the running release, so bumping `hamilton/version.py` can turn a warning into a failure; drive this scenario after a version bump.
