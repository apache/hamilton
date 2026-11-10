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
kind: suite
covers: .
---
# Project checks

The checks `.github/workflows/hamilton-main.yml` runs on every pull request that touches the library: prek's static checks and one test step per area. Each scenario runs its step's own commands, and an area recipe that names the same step copies the scenario word for word, which the `recipes-match-ci` scenario of `verify-tool` checks. This recipe lists, runs, and records them in the same place as every area.

## How a user reaches it

- Pull requests to `main` that touch a path in the workflow's `pull_request` filter run these in GitHub Actions: the static checks on one Python, the tests on every Python in the test job's matrix. The same jobs run daily on `main` and by hand, which the `ci-canary` recipe checks.
- Contributors call `uv run pytest ...` and `prek run` directly while iterating; the evidence a change rests on is a drive of this recipe or of the area recipe that names the same step.

## Scenarios

### static-checks
Run: `uv sync --dev && uv run prek run --all-files --hook-stage pre-merge-commit`
Proves: every prek hook the pre-merge-commit stage runs passes on every tracked file without changing one, as CI's *Check linting with prek* step runs it. Those hooks are ruff check and format; requirements sorting; the checks that Python files parse to an abstract syntax tree (AST) and that TOML (Tom's Obvious Minimal Language) files parse; the Apache Software Foundation (ASF) license headers; validation of the example notebooks; and the ruff and black hooks of `ui/sdk`.

### main
Run: `command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH (CI installs graphviz)' >&2; exit 3; }; uv sync --group test && uv run pytest tests/ --cov=hamilton --ignore tests/integrations || exit $(($? == 3 ? 1 : $?))`
Proves: the main package's tests under `tests/`, minus `tests/integrations`, pass with the `test` dependency group, as CI's *Test hamilton main package* step runs them.

### integrations
Run: `uv sync --group test --extra pandera && uv pip install -r tests/integrations/pandera/requirements.txt && uv run pytest tests/integrations || exit $(($? == 3 ? 1 : $?))`
Proves: the pandera integration tests pass with the `pandera` extra and the packages `tests/integrations/pandera/requirements.txt` lists, as CI's *Test integrations* step runs them.

### mcp
Run: `uv sync --group test --extra mcp && uv run pytest tests/plugins/test_h_mcp.py || exit $(($? == 3 ? 1 : $?))`
Proves: the Model Context Protocol (MCP) server tests pass with the `mcp` extra, as CI's *Test MCP* step runs them.

### openlineage
Run: `test -n "$HAMILTON_TEST_POSTGRES_URL" || { echo 'needs a PostgreSQL server named by HAMILTON_TEST_POSTGRES_URL; verify help openlineage says how to start one' >&2; exit 3; }; uv sync --group test --extra openlineage && uv pip install psycopg2-binary && uv run pytest tests/io/test_utils.py tests/plugins/test_pandas_extensions.py tests/plugins/test_h_openlineage.py || exit $(($? == 3 ? 1 : $?))`
Proves: the OpenLineage adapter, the pandas SQL loaders' lineage, and `hamilton.io.utils` pass against a real PostgreSQL server, as CI's *Test openlineage* step runs them.

### pandas
Run: `uv sync --group test && uv run pytest plugin_tests/h_pandas || exit $(($? == 3 ? 1 : $?))`
Proves: the `h_pandas.with_columns` integration tests pass, as CI's *Test pandas* step runs them.

### polars
Run: `uv sync --group test && uv pip install polars && uv run pytest plugin_tests/h_polars || exit $(($? == 3 ? 1 : $?))`
Proves: the `h_polars` and `h_polars_lazyframe` `with_columns` integration tests pass on the newest polars, as CI's *Test polars* step runs them.

### polars-1x
Run: `uv sync --group test && uv pip install 'polars<2' && uv run --no-sync python -c "import polars; assert polars.__version__.startswith('1.'), polars.__version__; print('polars', polars.__version__)" && uv run --no-sync pytest tests/plugins/test_polars_extensions.py tests/plugins/test_polars_lazyframe_extensions.py || exit $(($? == 3 ? 1 : $?))`
Proves: the readers and writers Hamilton registers for polars 1.x pass the polars and lazyframe extension tests on the newest polars 1 release, as CI's *Test polars 1.x readers* step runs them.

### narwhals
Run: `uv sync --group test && uv pip install polars pandas narwhals && uv run pytest plugin_tests/h_narwhals || exit $(($? == 3 ? 1 : $?))`
Proves: the narwhals adapter's integration tests pass over pandas and polars, as CI's *Test narwhals* step runs them.

### dask
Run: `uv sync --group test --extra dask && uv run pytest plugin_tests/h_dask || exit $(($? == 3 ? 1 : $?))`
Proves: the dask graph adapter, result builder, and executor integration tests pass with the `dask` extra, as CI's *Test dask* step runs them.

### ray
Run: `uv run --no-sync python -c 'import sys; sys.exit(sys.version_info >= (3, 15))' || { echo 'the ray extra installs ray only on Python 3.14 or older, and CI skips it on newer: uv sync --python 3.14 first' >&2; exit 3; }; uv sync --group test --extra ray && RAY_ENABLE_UV_RUN_RUNTIME_ENV=0 uv run pytest plugin_tests/h_ray || exit $(($? == 3 ? 1 : $?))`
Proves: the ray graph adapter, task executor, and remote-option parsing tests pass with the `ray` extra, as CI's *Test ray* step runs them.

### pyspark
Run: `command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH (CI installs graphviz)' >&2; exit 3; }; command -v java >/dev/null || { echo 'needs a Java runtime: java is not on PATH (CI installs default-jre)' >&2; exit 3; }; uv sync --group test --extra pyspark && uv pip install 'pyspark[connect]' 'grpcio' && uv pip install --no-cache --reinstall --strict 'grpcio-status >= 1.48.1' && PYSPARK_SUBMIT_ARGS='--conf spark.sql.ansi.enabled=false pyspark-shell' uv run pytest plugin_tests/h_spark || exit $(($? == 3 ? 1 : $?))`
Proves: the pyspark adapters, `h_spark.with_columns`, and `h_schema` integration tests pass with the `pyspark` extra and Spark Connect, as CI's *Test pyspark* step runs them on Linux.

### vaex
Run: `uv run --no-sync python -c 'import sys; sys.exit(sys.version_info[:2] not in ((3, 11), (3, 12)))' || { echo 'CI runs vaex only on Python 3.11 and 3.12: uv sync --python 3.12 first' >&2; exit 3; }; uv sync --group test && uv pip install "vaex>=4.19" && uv run --no-sync pytest plugin_tests/h_vaex || exit $(($? == 3 ? 1 : $?))`
Proves: the vaex result builder's integration tests pass with vaex 4.19 or newer, as CI's *Test vaex* step runs them.

## Gotchas

- It covers the whole tree, so `verify affected` names it for every change; it never counts as covering a path, which the area recipes do.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
- CI runs `static-checks` on one Python and the tests on every Python in the test job's matrix; a drive runs on whatever Python `.venv` has, which `verify doctor` checks against that matrix. A fresh `.venv` gets the newest Python uv finds, which can be outside it: `uv sync --python <a version in the matrix>` pins one inside.
- `static-checks` runs ruff with `--fix`, ruff format, the requirements sorter, and the license inserter: when they find something they rewrite tracked files and the run fails. Read `git diff` after a failed run and keep or drop the fixes; a rerun then passes.
- The trailing-whitespace and end-of-file hooks declare their own stages, which leave out pre-merge-commit, so neither CI nor this scenario runs them; `prek run --files <paths>` (the pre-commit stage) does.
- prek checks tracked files only, so a new file is not linted until it is added to git (`git add -N` is enough).
- The repository commits no `uv.lock`, so CI resolves the newest release of every dependency on each run, and a drive here can install different versions than a CI run on another day. `uv sync` writes an untracked `uv.lock` on its first run and reuses its pins after that, so delete it to resolve as CI does; leave it out of commits.
- Steps that add packages with `uv pip install` after their `uv sync` (`integrations`, `openlineage`, `polars`, `polars-1x`, `narwhals`, `pyspark`, `vaex`) do the same here; the next scenario's exact `uv sync` removes them again.
- Lines that start with `sudo apt-get` in CI are prerequisite checks here: a missing Graphviz (`main`, `pyspark`) or Java (`pyspark`) makes the scenario exit 3, which reads as unreachable, never as passed.
- CI's job also sets `HAMILTON_TELEMETRY_ENABLED=false`; telemetry has been removed (`hamilton/telemetry.py` is a no-op stub), so the scenarios leave it out.
- `openlineage` needs a PostgreSQL server; `verify help openlineage` says how to start a local one. Without `HAMILTON_TEST_POSTGRES_URL` its SQL tests would skip and the run would pass on less than CI checks, so the scenario exits 3 instead.
- `ray` and `vaex` check the Python version first and exit 3 where CI's step does not run them. The other scenarios run on every Python CI tests, as CI's steps do. The `recipes-match-ci` scenario of `verify-tool` checks that each scenario's Python check matches its step's `if:` condition.
- Every scenario that ends in pytest appends `|| exit $(($? == 3 ? 1 : $?))`: pytest exits 3 on an internal error, which the harness would read as unreachable, so the suffix turns it into 1 and passes every other code through.
- A change under `examples/` triggers this workflow, and `static-checks` is the check that runs on it; no area recipe covers `examples/`, so `verify affected` lists such a change as uncovered.
- Driving every scenario in a row reshapes `.venv` a dozen times and pulls large extras (ray, pyspark, vaex). Drive the scenarios `verify affected` points at; run the whole suite before a pull request.
