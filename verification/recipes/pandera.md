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
covers: hamilton/plugins/h_pandera.py, hamilton/data_quality/pandera_validators.py, tests/integrations
---
# Pandera schemas as output checks

A user validates a node's pandas, dask, or polars output against a pandera schema, given in `@check_output` or as the function's return type.

## How a user reaches it

- `@check_output(schema=pa.DataFrameSchema(...))`.
- `@h_pandera.check_output()` on a function whose return type is a pandera `DataFrame[Model]`.

## Scenarios

### integrations
Run: `uv sync --group test --extra pandera && uv pip install -r tests/integrations/pandera/requirements.txt && uv run pytest tests/integrations || exit $(($? == 3 ? 1 : $?))`
Proves: the pandera integration tests pass with the `pandera` extra and the packages `tests/integrations/pandera/requirements.txt` lists, as CI's *Test integrations* step runs them.

## Gotchas

- Its scenario is the suite's `integrations` scenario word for word; keep the two identical when CI's step changes. The `recipes-match-ci` scenario of `verify-tool` checks that they match.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
