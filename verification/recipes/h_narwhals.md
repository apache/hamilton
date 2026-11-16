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
covers: hamilton/plugins/h_narwhals.py, plugin_tests/h_narwhals
---
# Dataframe-agnostic code with narwhals

A user writes nodes against narwhals and runs the same dataflow over pandas or polars data.

## How a user reaches it

- `driver.Builder().with_adapters(h_narwhals.NarwhalsAdapter(), h_narwhals.NarwhalsDataFrameResultBuilder(...))`.

## Scenarios

### narwhals
Run: `uv sync --group test && uv pip install polars pandas narwhals && uv run pytest plugin_tests/h_narwhals || exit $(($? == 3 ? 1 : $?))`
Proves: the narwhals adapter's integration tests pass over pandas and polars, as CI's *Test narwhals* step runs them.

## Gotchas

- Its scenario is the suite's `narwhals` scenario word for word; keep the two identical when CI's step changes.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
