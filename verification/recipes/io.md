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
covers: hamilton/io, tests/io
---
# Load and save data

A user loads node inputs from files or databases and saves node outputs through registered data adapters, from decorators or from the driver.

## How a user reaches it

- `@load_from.<kind>(...)` and `@save_to.<kind>(...)` decorators.
- `dr.materialize(to.<kind>(...), from_.<kind>(...))` with `hamilton.io.materialization.to` and `from_`.
- `@dataloader` and `@datasaver` functions, and `hamilton.registry` for adapters plugins add.

## Scenarios

### tests
Run: `uv sync --group test && uv run pytest tests/io || exit $(($? == 3 ? 1 : $?))`
Proves: the data adapter contract, the default loaders and savers, materialization, and the IO metadata helpers pass their tests.

## Gotchas

- Its scenario runs part of the suite's `main` scenario, CI's *Test hamilton main package* step, without coverage: quick enough to run after every edit. The suite's `main` is the check CI runs.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- The SQL lineage tests in `tests/io/test_utils.py` skip without `HAMILTON_TEST_POSTGRES_URL`; the `openlineage` recipe runs them against a real server.
