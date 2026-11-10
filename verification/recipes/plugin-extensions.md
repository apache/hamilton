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
covers: hamilton/plugins, tests/plugins
---
# Plugin extensions

The adapters, result builders, and data loaders Hamilton ships for third-party libraries: numpy, pyarrow, pydantic, plotly, matplotlib, sklearn plots, xgboost, lightgbm, mlflow, kedro, dlt, huggingface, yaml, diskcache, datadog, tqdm, logging, the thread pool, and the rest.

## How a user reaches it

- `from hamilton.plugins import h_<name>` for adapters and helpers.
- `@load_from.<kind>` and `@save_to.<kind>` kinds, and `to.<kind>` and `from_.<kind>` materializers, that `<library>_extensions` modules register when their library is installed.

## Scenarios

### tests
Run: `uv sync --group test && uv run pytest tests/plugins || exit $(($? == 3 ? 1 : $?))`
Proves: the plugin unit tests that the `test` dependency group can run pass.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- On the Pythons where `tests/conftest.py` fills its `collect_ignore` list, because the `test` group does not install those files' packages there, a run over `tests/` leaves them out, so the scenario passes without running them; drive on a Python where the list is empty when the change touches them.
- `tests/plugins/test_h_mcp.py` and `tests/plugins/test_h_openlineage.py` skip here because the `test` group lacks their extras; the `mcp` and `openlineage` recipes run them for real.
- The libraries with integration suites under `plugin_tests/` have recipes of their own (`h_pandas`, `h_polars`, `h_narwhals`, `h_dask`, `h_ray`, `h_spark`, `h_vaex`).
