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
covers: hamilton/plugins/h_pandas.py, plugin_tests/h_pandas
---
# pandas with_columns

A user builds new pandas DataFrame columns from a subdag of functions and appends them to a DataFrame node.

## How a user reaches it

- `@h_pandas.with_columns(*modules, columns_to_pass=[...], select=[...])` on a function that takes the DataFrame.

## Scenarios

### pandas
Run: `uv sync --group test && uv run pytest plugin_tests/h_pandas || exit $(($? == 3 ? 1 : $?))`
Proves: the `h_pandas.with_columns` integration tests pass, as CI's *Test pandas* step runs them.

## Gotchas

- Its scenario is the suite's `pandas` scenario word for word; keep the two identical when CI's step changes.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- The pandas data loaders and savers (`hamilton/plugins/pandas_extensions.py`) are checked by `openlineage` and `plugin-extensions`.
