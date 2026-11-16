# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest>=8", "pyyaml>=6"]
# ///
"""Tests for `check_recipes_match_ci.py`.

Each test copies what the checker reads into a fresh root, changes one thing, and runs the
checker on that root through its `--root` option, asserting its exit code and every line it
prints. Run it with `uv run --script verification/scripts/test_check_recipes_match_ci.py`.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
CHECKER_PATH = HERE / "check_recipes_match_ci.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_recipes_match_ci", CHECKER_PATH)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves the module's string annotations through sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = _load_checker()

WORKFLOW = checker.WORKFLOW
SUFFIX = checker.PYTEST_SUFFIX
DASK_SYNC = "uv sync --group test --extra dask"
DASK_PYTEST = "uv run pytest plugin_tests/h_dask"
DASK_RUN = f"{DASK_SYNC} && {DASK_PYTEST}{SUFFIX}"
STEP_MISMATCH = "(apart from prerequisite checks and NAME=value prefixes)"


@pytest.fixture
def root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A copy of everything the checker reads: the recipes and the workflow."""
    shutil.copytree(REPO / "verification/recipes", tmp_path / "verification/recipes")
    (tmp_path / WORKFLOW).parent.mkdir(parents=True)
    shutil.copy2(REPO / WORKFLOW, tmp_path / WORKFLOW)
    return tmp_path


def mutate(root: pathlib.Path, path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    assert text.count(old) == 1, f"{path} holds {text.count(old)} copies of {old!r}, not one"
    target.write_text(text.replace(old, new))


def run_checker(root: pathlib.Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.stderr == ""
    return result.returncode, result.stdout


def assert_mismatches(root: pathlib.Path, *problems: str) -> None:
    summary = f"recipes-match-ci: {len(problems)} mismatch(es)"
    assert run_checker(root) == (1, "\n".join([*problems, summary]) + "\n")


def test_the_tree_as_committed_matches(root):
    code, stdout = run_checker(root)
    assert code == 0, stdout
    assert re.fullmatch(
        rf"recipes-match-ci: ok: [1-9]\d* suite scenarios run their {re.escape(WORKFLOW)} steps; "
        r"[1-9]\d* area scenarios in [1-9]\d* recipes match the suite\n",
        stdout,
    )


def run_pythons(root: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER_PATH), "--root", str(root), "--pythons"],
        capture_output=True,
        text=True,
        check=False,
    )


def test_pythons_prints_the_test_jobs_matrix(root):
    jobs = checker.yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    listed = checker.matrix_pythons(jobs["test"])
    assert listed
    result = run_pythons(root)
    assert (result.returncode, result.stdout, result.stderr) == (0, " ".join(listed) + "\n", "")


def test_pythons_reads_the_yaml_and_only_the_test_job(root):
    # A trailing comment and double quotes are still the same entry; another job's list is not
    # the test job's.
    jobs = checker.yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    listed = checker.matrix_pythons(jobs["test"])
    newest = listed[-1]
    mutate(root, WORKFLOW, f"          - '{newest}'\n", f'          - "{newest}" # newest\n')
    mutate(
        root,
        WORKFLOW,
        "\n  notify-slack:\n",
        "\n  test_windows_2:\n    strategy:\n      matrix:\n        python-version: ['3.10']\n"
        "    steps:\n      - run: echo\n\n  notify-slack:\n",
    )
    result = run_pythons(root)
    assert (result.returncode, result.stderr) == (0, "")
    assert result.stdout.split() == listed


def test_pythons_fails_when_the_test_job_lists_none(root):
    jobs = checker.yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    entries = "".join(f"          - '{v}'\n" for v in checker.matrix_pythons(jobs["test"]))
    mutate(root, WORKFLOW, "        python-version:\n" + entries, "")
    result = run_pythons(root)
    assert (result.returncode, result.stdout) == (1, "")
    assert result.stderr == f"{WORKFLOW}: job 'test' lists no python-version matrix\n"


def test_a_changed_workflow_command_is_named(root):
    mutate(root, WORKFLOW, DASK_PYTEST, "uv run pytest -x plugin_tests/h_dask")
    assert_mismatches(
        root,
        f"suite.md: scenario dask: runs {[DASK_SYNC, DASK_PYTEST]} but step 'Test dask' runs "
        f"{[DASK_SYNC, 'uv run pytest -x plugin_tests/h_dask']} {STEP_MISMATCH}",
    )


def test_an_area_copy_that_differs_from_its_suite_scenario_is_named(root):
    mutate(
        root, "verification/recipes/h_dask.md", DASK_PYTEST, "uv run pytest -x plugin_tests/h_dask"
    )
    assert_mismatches(
        root,
        "h_dask.md: scenario dask: is not suite dask word for word:\n"
        f"    here:  {DASK_SYNC} && uv run pytest -x plugin_tests/h_dask{SUFFIX}\n"
        f"    suite: {DASK_RUN}",
    )


def test_a_workflow_step_running_uv_needs_a_suite_scenario(root):
    new_step = (
        "        - name: Test something new\n"
        "          run: |\n"
        "            uv sync --group test\n"
        "            uv run pytest plugin_tests/h_new\n"
        "\n"
    )
    mutate(root, WORKFLOW, "        - name: Test ray\n", new_step + "        - name: Test ray\n")
    assert_mismatches(root, f"suite.md: no scenario runs {WORKFLOW} step 'Test something new'")


RAY_GUARD = "sys.version_info >= (3, 15)"
RAY_IF = "matrix.python-version == '3.13' || matrix.python-version == '3.14' }}"


def test_a_python_check_that_lets_through_other_versions_than_its_step_is_named(root):
    for recipe in ("suite", "h_ray"):
        mutate(root, f"verification/recipes/{recipe}.md", RAY_GUARD, "sys.version_info >= (3, 14)")
    assert_mismatches(
        root,
        "suite.md: scenario ray: runs on Python 3.11, 3.12, 3.13, "
        "but step 'Test ray' runs on 3.11, 3.12, 3.13, 3.14",
    )


def test_a_changed_step_condition_is_named(root):
    mutate(root, WORKFLOW, RAY_IF, "matrix.python-version == '3.13' }}")
    assert_mismatches(
        root,
        "suite.md: scenario ray: runs on Python 3.11, 3.12, 3.13, 3.14, "
        "but step 'Test ray' runs on 3.11, 3.12, 3.13",
    )


def test_a_strict_python_check_is_read_as_python_reads_it(root):
    # On 3.14.0, sys.version_info is (3, 14, 0, 'final', 0), which is greater than (3, 14).
    for recipe in ("suite", "h_ray"):
        mutate(root, f"verification/recipes/{recipe}.md", RAY_GUARD, "sys.version_info > (3, 14)")
    assert_mismatches(
        root,
        "suite.md: scenario ray: runs on Python 3.11, 3.12, 3.13, "
        "but step 'Test ray' runs on 3.11, 3.12, 3.13, 3.14",
    )


def test_a_step_condition_that_leaves_versions_out_is_read(root):
    mutate(
        root,
        WORKFLOW,
        "matrix.python-version == '3.11' || matrix.python-version == '3.12' || " + RAY_IF,
        "matrix.python-version != '3.15' }}",
    )
    code, stdout = run_checker(root)
    assert code == 0, stdout


def test_a_step_condition_leaving_out_several_versions_is_read_as_a_conjunction(root):
    mutate(
        root,
        WORKFLOW,
        "matrix.python-version == '3.11' || matrix.python-version == '3.12' || " + RAY_IF,
        "matrix.python-version != '3.15' && matrix.python-version != '3.11' }}",
    )
    assert_mismatches(
        root,
        "suite.md: scenario ray: runs on Python 3.11, 3.12, 3.13, 3.14, "
        "but step 'Test ray' runs on 3.12, 3.13, 3.14",
    )


def test_a_step_condition_reading_the_matrix_by_index_is_named(root):
    condition = "matrix['python-version'] != '3.15' }}"
    mutate(
        root,
        WORKFLOW,
        "matrix.python-version == '3.11' || matrix.python-version == '3.12' || " + RAY_IF,
        condition,
    )
    assert_mismatches(
        root,
        "suite.md: scenario ray: step 'Test ray' has an if: condition this check cannot read: "
        f'"${{{{ {condition}"',
    )


def test_a_step_condition_spelling_the_matrix_in_capitals_is_read(root):
    mutate(
        root,
        WORKFLOW,
        "matrix.python-version == '3.11' || matrix.python-version == '3.12' || " + RAY_IF,
        "Matrix.Python-Version == '3.13' }}",
    )
    assert_mismatches(
        root,
        "suite.md: scenario ray: runs on Python 3.11, 3.12, 3.13, 3.14, "
        "but step 'Test ray' runs on 3.13",
    )


def test_a_step_condition_reading_the_whole_matrix_is_named(root):
    condition = "contains(toJSON(matrix), '3.13') }}"
    mutate(
        root,
        WORKFLOW,
        "matrix.python-version == '3.11' || matrix.python-version == '3.12' || " + RAY_IF,
        condition,
    )
    assert_mismatches(
        root,
        "suite.md: scenario ray: step 'Test ray' has an if: condition this check cannot read: "
        f'"${{{{ {condition}"',
    )


def test_a_step_condition_beyond_the_forms_it_reads_is_named(root):
    mutate(root, WORKFLOW, RAY_IF, "matrix.python-version == '3.13' || always() }}")
    assert_mismatches(
        root,
        "suite.md: scenario ray: step 'Test ray' has an if: condition this check cannot read: "
        "\"${{ matrix.python-version == '3.11' || matrix.python-version == '3.12' || "
        "matrix.python-version == '3.13' || always() }}\"",
    )


def test_a_matrix_python_it_cannot_compare_is_named_once(root):
    mutate(root, WORKFLOW, "          - '3.15'\n", "          - '3.15'\n          - '3.16-dev'\n")
    assert_mismatches(
        root,
        f"{WORKFLOW}: job 'test' tests Pythons this check cannot compare: ['3.16-dev']; "
        "it reads MAJOR.MINOR versions only",
    )


def test_a_python_check_on_a_step_without_a_matrix_is_named(root):
    mutate(
        root,
        "verification/recipes/suite.md",
        "Run: `uv sync --dev && ",
        "Run: `uv run --no-sync python -c 'import sys; sys.exit(sys.version_info >= (3, 15))' "
        "|| { echo 'x' >&2; exit 3; }; uv sync --dev && ",
    )
    assert_mismatches(
        root,
        "suite.md: scenario static-checks: checks the Python version, "
        "but step 'Check linting with prek' has no Python matrix",
    )


def test_a_step_installing_system_packages_needs_a_command_check(root):
    command_checks = (
        "command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH "
        "(CI installs graphviz)' >&2; exit 3; }; command -v java >/dev/null || { echo 'needs a "
        "Java runtime: java is not on PATH (CI installs default-jre)' >&2; exit 3; }; "
    )
    # A Python version check that lets every version through is a prerequisite, but not a check
    # for the Java runtime the step installs with apt-get.
    version_check = (
        "uv run --no-sync python -c 'import sys; sys.exit(sys.version_info < (3, 0))' "
        "|| { echo 'x' >&2; exit 3; }; "
    )
    for recipe in ("suite", "h_spark"):
        mutate(root, f"verification/recipes/{recipe}.md", command_checks, version_check)
    jobs = checker.yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    step = next(s for s in jobs["test"]["steps"] if s.get("name") == "Test pyspark")
    _, apt = checker.step_commands(step)
    assert apt
    assert_mismatches(
        root,
        f"suite.md: scenario pyspark: step 'Test pyspark' installs system packages ({apt}); "
        "check for them and exit 3 when they are missing",
    )


@pytest.mark.parametrize(
    ("condition", "on_linux"),
    [
        (None, True),
        ("runner.os == 'Linux'", True),
        ("${{ runner.os == 'linux' }}", True),
        ("runner.os != 'Windows'", True),
        ("${{ runner.os != 'Linux' }}", False),
        ("runner.os == 'macOS'", False),
        ("runner.os == 'macOS' || runner.os == 'Linux'", True),
        ("runner.os != 'Windows' && runner.os != 'macOS'", True),
        ("runner.os != 'Linux' && runner.os != 'Windows'", False),
        ("Runner.OS == 'Windows'", False),
    ],
)
def test_a_step_runs_on_linux_as_github_compares_runner_os(condition, on_linux):
    step = {} if condition is None else {"if": condition}
    assert checker.runs_on_linux(step) is on_linux


def test_a_scenario_naming_a_step_that_runs_only_apt_lines_is_compared_without_a_crash(root):
    step_name = "Install Graphviz on Linux"
    mutate(
        root, "verification/recipes/suite.md", "CI's *Test dask* step", f"CI's *{step_name}* step"
    )
    jobs = checker.yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    step = next(s for s in jobs["test"]["steps"] if s.get("name") == step_name)
    commands, apt = checker.step_commands(step)
    assert commands == [] and apt
    assert_mismatches(
        root,
        f"suite.md: scenario dask: runs {[DASK_SYNC, DASK_PYTEST + SUFFIX]} but step '{step_name}' "
        f"runs [] {STEP_MISMATCH}",
        f"suite.md: scenario dask: step '{step_name}' installs system packages ({apt}); "
        "check for them and exit 3 when they are missing",
        f"suite.md: no scenario runs {WORKFLOW} step 'Test dask'",
    )


def test_a_scenario_without_the_pytest_exit_mapping_is_named(root):
    mutate(
        root,
        "verification/recipes/cli.md",
        f"uv run pytest tests/cli{SUFFIX}",
        "uv run pytest tests/cli",
    )
    assert_mismatches(
        root, f"cli.md: scenario tests: Run line must end with the pytest exit-3 mapping '{SUFFIX}'"
    )


@pytest.mark.parametrize(
    ("recipe", "scenario", "claim"),
    [
        ("h_dask", "dask", "Its scenario is the suite's `dask` scenario word for word"),
        ("cli", "tests", "Its scenario runs part of the suite's `main` scenario"),
    ],
)
def test_a_scenario_without_a_gotchas_claim_is_named(root, recipe, scenario, claim):
    mutate(root, f"verification/recipes/{recipe}.md", claim, "Its scenario resembles CI")
    assert_mismatches(
        root,
        f"{recipe}.md: scenario {scenario}: its Gotchas must say it is a suite scenario word for "
        "word or runs part of the suite's `main` scenario",
    )


def test_a_scoped_part_of_main_may_not_run_tests_integrations(root):
    mutate(
        root,
        "verification/recipes/cli.md",
        "uv run pytest tests/cli ",
        "uv run pytest tests/cli tests/integrations/pandera ",
    )
    assert_mismatches(
        root,
        "cli.md: scenario tests: runs ['tests/integrations/pandera'], which suite main does not run",
    )


def test_a_step_env_value_the_scenario_does_not_set_is_named(root):
    mutate(root, WORKFLOW, "RAY_ENABLE_UV_RUN_RUNTIME_ENV: 0 ", "RAY_ENABLE_UV_RUN_RUNTIME_ENV: 1 ")
    assert_mismatches(
        root,
        "suite.md: scenario ray: sets RAY_ENABLE_UV_RUN_RUNTIME_ENV='0', but the step sets '1'",
    )


@pytest.mark.parametrize(
    "fallback", ["|| exit 3", "|| { echo 'missing' >&2; exit 3; }"], ids=["bare", "braced"]
)
def test_a_command_with_an_exit_3_fallback_is_compared_like_any_other(root, fallback):
    extra = f"uv pip install evil {fallback}"
    for recipe in ("suite", "h_dask"):
        mutate(
            root,
            f"verification/recipes/{recipe}.md",
            f"{DASK_SYNC} && {DASK_PYTEST}",
            f"{DASK_SYNC} && {extra} && {DASK_PYTEST}",
        )
    assert_mismatches(
        root,
        f"suite.md: scenario dask: runs {[DASK_SYNC, extra, DASK_PYTEST]} but step 'Test dask' "
        f"runs {[DASK_SYNC, DASK_PYTEST]} {STEP_MISMATCH}",
    )


def test_a_scoped_part_of_main_may_not_add_a_command_with_an_exit_3_fallback(root):
    mutate(
        root,
        "verification/recipes/cli.md",
        "uv sync --group test && uv run pytest tests/cli",
        "uv sync --group test && uv pip install evil || exit 3 && uv run pytest tests/cli",
    )
    assert_mismatches(
        root,
        "cli.md: scenario tests: must run suite main's `uv sync --group test`, "
        "then `uv run pytest <paths>`",
    )


def committed_prerequisites() -> list[str]:
    """Every segment of a committed Run line that exits 3, the pytest exit mapping aside."""
    found = set()
    for path in sorted((REPO / "verification/recipes").glob("*.md")):
        for scenario in checker.parse_recipe(path).scenarios:
            run = scenario.run.removesuffix(SUFFIX)
            for segment in checker.segments(run):
                if "exit 3" in segment:
                    found.add(segment)
    return sorted(found)


@pytest.mark.parametrize("segment", committed_prerequisites())
def test_every_committed_prerequisite_check_is_recognized(segment):
    assert checker.is_prerequisite(segment)


@pytest.mark.parametrize(
    "segment",
    [
        "uv pip install evil || exit 3",
        "uv pip install evil || { echo 'missing' >&2; exit 3; }",
        "command -v dot >/dev/null || { echo 'x' >&2; exit 3; }; uv pip install evil",
        "command -v dot >/dev/null || { echo 'x' >&2; uv pip install evil; exit 3; }",
        "test -n \"$(uv pip install evil)\" || { echo 'x' >&2; exit 3; }",
        "uv run --no-sync python -c 'import os; os.system(\"evil\")' || { echo 'x' >&2; exit 3; }",
        (
            "uv run --no-sync python -c 'import sys; sys.exit(sys.version_info >= (3, 14)); "
            "import os' || { echo 'x' >&2; exit 3; }"
        ),
        (
            "{ .venv/bin/python -c 'import sys; sys.exit(sys.version_info >= (3, 14))' || "
            "{ echo 'x' >&2; exit 3; }; }"
        ),
    ],
    ids=[
        "bare-fallback",
        "braced-fallback",
        "command-after-check",
        "command-inside-fallback",
        "command-substitution-in-test",
        "python-not-a-version-test",
        "python-after-version-test",
        "braced-venv-python",
    ],
)
def test_other_commands_are_not_prerequisite_checks(segment):
    assert not checker.is_prerequisite(segment)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-p", "no:cacheprovider"]))
