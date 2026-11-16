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
covers: hamilton/plugins/h_polars.py, hamilton/plugins/h_polars_lazyframe.py, hamilton/plugins/polars_extensions.py, hamilton/plugins/polars_implementations.py, hamilton/plugins/polars_lazyframe_extensions.py, hamilton/plugins/polars_lazyframe_post_2_0_0_extensions.py, hamilton/plugins/polars_lazyframe_pre_2_0_0_extensions.py, hamilton/plugins/polars_post_1_0_0_extensions.py, hamilton/plugins/polars_post_2_0_0_extensions.py, hamilton/plugins/polars_pre_1_0_0_extension.py, plugin_tests/h_polars, tests/plugins/test_polars_extensions.py, tests/plugins/test_polars_lazyframe_extensions.py
---
# Polars dataframes

A user builds polars DataFrames and LazyFrames from Hamilton nodes, appends columns from a subdag, and reads and writes polars data through materializers.

## How a user reaches it

- `@h_polars.with_columns(...)` and `@h_polars_lazyframe.with_columns(...)`.
- `h_polars.PolarsDataFrameResult()` and `h_polars_lazyframe.PolarsLazyFrameResult()` as the driver's result builder.
- `@load_from` / `@save_to` and `from_` / `to` kinds for polars (parquet, csv, feather, json, ndjson, avro, spreadsheet, database), registered when polars is installed.

## Scenarios

### polars
Run: `uv sync --group test && uv pip install polars && uv run pytest plugin_tests/h_polars || exit $(($? == 3 ? 1 : $?))`
Proves: the `h_polars` and `h_polars_lazyframe` `with_columns` integration tests pass on the newest polars, as CI's *Test polars* step runs them.

### extensions
Run: `uv sync --group test && uv run pytest tests/plugins/test_polars_extensions.py tests/plugins/test_polars_lazyframe_extensions.py || exit $(($? == 3 ? 1 : $?))`
Proves: the polars and lazyframe data loaders and savers pass their unit tests on the `test` group's polars, part of CI's *Test hamilton main package* step.

### polars-1x
Run: `uv sync --group test && uv pip install 'polars<2' && uv run --no-sync python -c "import polars; assert polars.__version__.startswith('1.'), polars.__version__; print('polars', polars.__version__)" && uv run --no-sync pytest tests/plugins/test_polars_extensions.py tests/plugins/test_polars_lazyframe_extensions.py || exit $(($? == 3 ? 1 : $?))`
Proves: the readers and writers Hamilton registers for polars 1.x pass the polars and lazyframe extension tests on the newest polars 1 release, as CI's *Test polars 1.x readers* step runs them.

## Gotchas

- Its `polars` scenario is the suite's `polars` scenario word for word. Its `polars-1x` scenario is the suite's `polars-1x` scenario word for word. Keep each identical to its suite scenario when CI's step changes. Its `extensions` scenario runs part of the suite's `main` scenario without coverage. The `recipes-match-ci` scenario of `verify-tool` checks all three.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
