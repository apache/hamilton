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
kind: tool
covers: scripts/verify, scripts/verify.mts, scripts/verify.test.mts, verification/harness.md, verification/recipes, verification/scripts/check_recipes_match_ci.py, verification/scripts/doctor.sh, verification/scripts/test_check_recipes_match_ci.py, .github/workflows/hamilton-main.yml
---
# The verification harness itself

A contributor or agent learns how to check Hamilton from `scripts/verify --help`, and the harness names the recipes a change touches and runs them. This recipe checks that the harness still reads its own recipes and settings, that its own code does what it says, that the recipes still run what CI runs, and that the source release leaves `scripts/verify` out.

## How a user reaches it

- `scripts/verify doctor`, which runs the same check and then the prerequisites in `verification/harness.md`.

## Scenarios

### check
Run: `scripts/verify check`
Proves: every recipe and the settings parse, and every path a recipe covers or a scenario names exists.

### doctor
Run: `doctor=$(sed -n 's/^doctor: //p' verification/harness.md) && { [ -n "$doctor" ] || { echo 'verification/harness.md declares no doctor: command' >&2; exit 1; }; } && d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && ln -s "$PWD/.github" "$PWD/verification" "$d" && mkdir -p "$d/.venv/bin" && printf '#!/bin/sh\necho 3.0\n' > "$d/.venv/bin/python" && chmod +x "$d/.venv/bin/python" && if (cd "$d" && sh -c "$doctor") > "$d/out" 2>&1; then echo 'doctor passed a .venv on Python 3.0, which CI does not test' >&2; exit 1; fi && { grep -q 'which CI does not test' "$d/out" || { cat "$d/out" >&2; exit 1; }; } && rm "$d/.github" && mkdir -p "$d/.github/workflows" && printf "jobs:\n  test:\n    strategy:\n      matrix:\n        python-version: ['3.0']\n" > "$d/.github/workflows/hamilton-main.yml" && (cd "$d" && sh -c "$doctor") || { echo 'doctor failed a .venv on Python 3.0 once the test job lists 3.0' >&2; exit 1; }`
Proves: the `doctor:` command `verification/harness.md` declares, which `verify doctor` runs, fails a `.venv` on a Python the test job of `.github/workflows/hamilton-main.yml` does not list, and passes the same `.venv` once the workflow lists its Python: it reads the workflow rather than a copy of the list.

### node-tests
Run: `node --test scripts/verify.test.mts`
Proves: the harness's own unit tests pass: how `check` reads recipes, how `affected` maps changed paths to recipes, and how `drive` runs scenarios and records their outcomes.

### recipes-match-ci
Run: `uv run --script verification/scripts/check_recipes_match_ci.py`
Proves: each `suite` scenario runs the commands of the `.github/workflows/hamilton-main.yml` step its Proves line names, on the Pythons that step's `if:` runs it on, and every step that runs uv has such a scenario. Each area scenario is a suite scenario word for word or a scoped part of the suite's `main`.

### recipes-match-ci-tests
Run: `uv run --script verification/scripts/test_check_recipes_match_ci.py`
Proves: the `recipes-match-ci` checker accepts the committed recipes and names each mismatch its tests plant in a copy of them, and its `--pythons` option, which `verify doctor` reads, prints the test job's matrix as the workflow's YAML states it.

### sdist
Run: `d=$(mktemp -d) && trap 'rm -rf "$d"' EXIT && uv build --sdist --out-dir "$d" >/dev/null && tar -tzf "$d"/*.tar.gz > "$d/listing" && sed 's|^[^/]*/||' "$d/listing" > "$d/files" && { ! grep -xE 'scripts/verify(\.mts|\.test\.mts)?' "$d/files" || { echo 'the sdist ships the files above without verification/ and .github/, which they read' >&2; exit 1; }; } && beside=$(git ls-files 'scripts/verify[-_]*') && { [ -n "$beside" ] || { echo 'git lists no tracked file that shares the scripts/verify prefix' >&2; exit 1; }; } && for f in $beside; do grep -qxF "$f" "$d/files" || { echo "the sdist lost $f, which shares the scripts/verify prefix but is not the harness" >&2; exit 1; }; done`
Proves: the `apache-hamilton` source release ships none of `scripts/verify`, `scripts/verify.mts` and `scripts/verify.test.mts`, which read `verification/` and `.github/` that it leaves out, and still ships every tracked file whose name starts `scripts/verify-` or `scripts/verify_`: the release scripts beside them.

## Gotchas

- The tool needs Node 22.18 or newer; `scripts/verify` exits 3 and says so when Node is missing or older, so a drive of `node-tests` always has a Node that runs it. CI runs neither the tool nor its Node tests, and no Python test calls them: this recipe is their only check.
- `sdist` checks the `scripts/verify` entries in the `exclude` list of `pyproject.toml`'s `[tool.flit.sdist]` table, and that the files sharing their prefix stay in. This recipe does not cover `pyproject.toml`, so that `verify affected` does not name it for every dependency change: drive `sdist` after editing that table's `scripts` entries.
- `recipes-match-ci` and `recipes-match-ci-tests` run in their own environments (`uv run --script` installs only PyYAML, and pytest for the tests), so they leave `.venv` as it was. When CI's workflow changes, `recipes-match-ci` names each scenario that no longer matches; change the `suite` scenario first, then the area scenarios that copy it.
- Every Markdown file here opens with the Apache Software Foundation (ASF) license comment the repository's insert-license hook requires; the tool skips that comment before reading front matter, so keep the comment first and the `---` front matter right after it.
