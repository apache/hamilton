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
covers: hamilton/plugins/h_vaex.py, hamilton/plugins/vaex_extensions.py, plugin_tests/h_vaex
---
# Vaex dataframes

A user collects Hamilton outputs into a vaex DataFrame and loads and saves vaex data.

## How a user reaches it

- `h_vaex.VaexDataFrameResult()` as the driver's result builder.

## Scenarios

### vaex
Run: `uv run --no-sync python -c 'import sys; sys.exit(sys.version_info[:2] not in ((3, 11), (3, 12)))' || { echo 'CI runs vaex only on Python 3.11 and 3.12: uv sync --python 3.12 first' >&2; exit 3; }; uv sync --group test && uv pip install "vaex>=4.19" && uv run --no-sync pytest plugin_tests/h_vaex || exit $(($? == 3 ? 1 : $?))`
Proves: the vaex result builder's integration tests pass with vaex 4.19 or newer, as CI's *Test vaex* step runs them.

## Gotchas

- Its scenario is the suite's `vaex` scenario word for word; keep the two identical when CI's step changes.
- CI runs this step only on the Pythons its `if:` names, the ones vaex supports; on any other Python the scenario exits 3 (unreachable), and its message names one to sync to. Sync back to your usual Python afterwards.
- `uv run --no-sync` runs the tests on exactly what the step installed, as CI's step does; a plain `uv run` would first sync the environment to the project's requirements.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
