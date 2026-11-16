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
ask-first: ask
doctor: sh verification/scripts/doctor.sh
---
- Every check here, apart from the harness's own checks in `verify-tool`, is adopted from `.github/workflows/hamilton-main.yml`. The `suite` recipe has one scenario per CI step, running that step's own commands. Each area recipe runs the same commands as its CI step, or a scoped part of the main package's test step for quick iteration. When CI's workflow changes, the `recipes-match-ci` scenario of `verify-tool` names each scenario that no longer matches it, including a Python version check that no longer matches its step's `if:`; change those with the workflow. The `ci-canary` recipe checks that workflow itself: its daily schedule and its Slack report, rehearsed under [act](https://nektosact.com), which runs GitHub Actions workflows locally.
- Nothing here is ask-first: every scenario runs local tests or static checks on this machine. `ci-canary` posts only to a local stub and reads one public run from api.github.com without credentials. The `openlineage` scenario writes only to the PostgreSQL server `HAMILTON_TEST_POSTGRES_URL` names, in a throwaway schema it drops; point it at a disposable local server (its recipe says how), never a shared one.
- What every run starts from: this checkout and its uv-managed `.venv`. Each scenario first runs its CI step's own `uv sync`, which is exact, so `.venv` ends shaped like the last scenario driven; `uv sync --group test` restores the usual test environment. Runs are isolated per worktree: two drives at once in one checkout share `.venv` and collide, so run side by side only from separate worktrees.
- Python: CI runs the static checks on one Python and the tests on every Python in the test job's matrix, which `verify doctor` reads from the workflow and checks `.venv` against. A drive runs on whatever Python `.venv` has; `uv sync --python <version>` changes it. A scenario whose CI step runs on only some of those Pythons, as ray's and vaex's do, checks the version first and exits 3 elsewhere; the step's `if:` and the scenario's message name the versions. On the Pythons where `tests/conftest.py` fills its `collect_ignore` list, a run over `tests/` leaves out the files it names, as CI's runs there do, so a scenario such as `plugin-extensions` passes there without running them: drive it on a Python where the list is empty when a change touches them.
- Prerequisites a scenario checks, exiting 3 (unreachable) when one is missing: Graphviz's `dot` (main package, `driver`, `graph`, and pyspark); Java (pyspark); a Python its CI step runs on (ray and vaex); `HAMILTON_TEST_POSTGRES_URL` (openlineage); and a Linux host with Docker, act, the GitHub command-line interface (`gh`), and `jq` (`ci-canary`). CI installs the system ones with apt; install them yourself. Exit 3 means unreachable and nothing else, but pytest exits 3 on an internal error. So every scenario that ends in pytest appends `|| exit $(($? == 3 ? 1 : $?))`, which turns pytest's 3 into a failure and passes every other code through.
- The repository commits no `uv.lock`: CI resolves the newest release of every dependency on each run. A drive's first `uv sync` writes an untracked `uv.lock` and every later one reuses its pins, so drives can run older versions than CI until it is deleted, which `verify doctor` points out. `verify affected` lists it among the changed paths; leave it out of commits.
- No control commands are declared: no scenario starts anything that outlives it. Each one is a self-contained test or lint run; the dask, ray, and Spark tests start their local instances in-process and stop them.
- `verify affected` lists a changed path as uncovered when no recipe other than `suite` covers it, as for everything under `ui/`, `contrib/`, `dev_tools/`, `docs/`, and `examples/`. A change under `examples/` triggers `hamilton-main.yml`, whose prek step (the suite's `static-checks`) lints it and validates the example notebooks: drive `static-checks` for it. A change to `scripts/render_redirect_pyproject.py` or an `sf-hamilton*-redirect/` directory triggers it too, and `tests/test_redirect_packages.py`, part of the suite's `main` scenario, checks them: `uv run pytest tests/test_redirect_packages.py` runs that file alone. `hamilton-contrib.yml` runs `contrib/tests` on pull requests that touch `contrib/`, `hamilton/`, `pyproject.toml`, or the workflow itself; no recipe adopts it. The others have workflows of their own that no recipe adopts: `hamilton-sdk.yml`, `hamilton-ui-backend.yml`, and `hamilton-ui-frontend.yml` for `ui/sdk/`, `ui/backend/`, and `ui/frontend/`; `sphinx-docs.yml` for `docs/`; `hamilton-lsp.yml` for `dev_tools/language_server/`; `contrib-auto-build-publish.yml` and `docusaurus-gh-pages.yml` for `contrib/`, on push only. `hamilton-ui-build-and-push.yml` builds the UI's images daily and by hand, whatever changed. No workflow is triggered by the rest of `ui/` or by `dev_tools/vscode_extension/`. `static-checks` lints every tracked file outside `docs/code-comparisons/`, including the paths above. CI runs it on a pull request only when the change touches a path in the `pull_request` filter of `hamilton-main.yml`; its daily and manual runs happen whatever changed.
