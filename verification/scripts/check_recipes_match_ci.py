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
# dependencies = ["pyyaml>=6"]
# ///
"""Check that the verification recipes still run what `.github/workflows/hamilton-main.yml` runs.

Three promises are checked:

1. Each `suite` scenario runs its workflow step's commands, in order and nothing else, apart
   from prerequisite checks, `NAME=value` prefixes taken from the step's `env:`, and the suffix
   that maps pytest's exit 3 to 1. A prerequisite check is `command -v NAME >/dev/null`,
   `test -n "$NAME"`, or a Python version test, followed by `|| { echo '...' >&2; exit 3; }`;
   any other command is compared with the step's, whatever its fallback. A step that installs
   system packages needs a `command -v` check. The scenario's Proves line names the step as
   ``CI's *<step name>* step``. Every workflow step that runs uv must have such a scenario.
2. Each area recipe (`kind: feature` or `kind: plugin`) says in its Gotchas, per scenario, either
   "Its [`name`] scenario is the suite's `X` scenario word for word" (its Run line then equals
   the Run line of suite scenario `X`) or "Its [`name`] scenario runs part of the suite's `main`
   scenario" (it then runs main's `uv sync` and pytest on paths under `tests/` outside
   `tests/integrations`).
3. Each `suite` scenario runs on the Pythons its step runs on: over its job's matrix, the Python
   version tests among its prerequisites let through exactly the versions the step's `if:`
   condition does.

Run it from anywhere with `uv run --script verification/scripts/check_recipes_match_ci.py
[--root DIR]`; it exits 0 when everything matches and 1 with one line per mismatch. With
`--pythons` it prints the Pythons the workflow's test job lists instead, which `verify doctor`
checks `.venv` against.
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import shlex
import sys

import yaml

# Appended to every Run line whose last command is pytest: pytest exits 3 on an internal error,
# which the harness would otherwise read as "unreachable".
PYTEST_SUFFIX = " || exit $(($? == 3 ? 1 : $?))"
WORKFLOW = ".github/workflows/hamilton-main.yml"
TEST_JOB = "test"
AREA_KINDS = {"feature", "plugin"}
CLAIM = re.compile(
    r"Its (?:`(?P<scenario>[\w-]+)` )?scenario "
    r"(?:is the suite's `(?P<copy>[\w-]+)` scenario word for word"
    r"|(?P<part>runs part of the suite's `main` scenario))"
)
# The prerequisite checks a Run line may add to its step's commands, anchored so that no other
# command passes as one: each exits 3 with a reason when its prerequisite is missing.
VERSION_TEST = (
    r"sys\.version_info(?:\[:2\])? (?:[<>]=?|(?:not )?in) "
    r"(?:\(\d+, \d+\)|\((?:\(\d+, \d+\), )*\(\d+, \d+\)\))"
)
PREREQUISITE = re.compile(
    r"(?:command -v [\w.+-]+ >/dev/null"
    r"|test -n \"\$[A-Za-z_]\w*\""
    rf"|uv run --no-sync python -c 'import sys; sys\.exit\({VERSION_TEST}\)')"
    r" \|\| \{ echo '[^']*' >&2; exit 3; \}"
)
VERSION_GUARD = re.compile(
    rf"uv run --no-sync python -c 'import sys; sys\.exit\((?P<test>{VERSION_TEST})\)'"
)
# The two forms of a step's `if:` on the matrix's Python that this check reads: versions named
# with `==` and joined by `||`, or versions left out with `!=` and joined by `&&`.
# GitHub reads context names without regard to case, so these do too. A condition that names
# the matrix context in any other way (`matrix['python-version']`, `toJSON(matrix)`) is not read.
MATRIX_READ = re.compile(r"\bmatrix\b", re.IGNORECASE)
PYTHON_IS = re.compile(r"matrix\.python-version == '([^']*)'", re.IGNORECASE)
PYTHON_IS_NOT = re.compile(r"matrix\.python-version != '([^']*)'", re.IGNORECASE)
OS_TEST = re.compile(r"runner\.os\s*(==|!=)\s*'([^']*)'", re.IGNORECASE)
MAJOR_MINOR = re.compile(r"\d+\.\d+")
STEP_NAMED = re.compile(r"CI's \*([^*]+)\* step")
ASSIGNMENT = re.compile(r"""^([A-Za-z_]\w*)=('[^']*'|"[^"]*"|\S+)\s+""")
PYTEST_VALUE_OPTIONS = {"--ignore", "--deselect", "-k", "-m", "-p", "--rootdir"}


@dataclasses.dataclass
class Scenario:
    recipe: str
    name: str
    run: str
    proves: str


@dataclasses.dataclass
class Recipe:
    name: str
    kind: str
    scenarios: list[Scenario]
    gotchas: str


def parse_recipe(path: pathlib.Path) -> Recipe:
    text = path.read_text()
    text = re.sub(r"\A\s*<!--.*?-->\s*", "", text, flags=re.DOTALL)  # the license comment
    front = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    meta = (
        dict(re.findall(r"^([\w-]+):\s*(.*)$", front.group(1), flags=re.MULTILINE)) if front else {}
    )
    body = text[front.end() :] if front else text

    def section(title: str) -> str:
        found = re.search(
            rf"^## {title}[ \t]*$(.*?)(?=^## |\Z)", body, flags=re.MULTILINE | re.DOTALL
        )
        return found.group(1) if found else ""

    scenarios = []
    for block in re.split(r"^### ", section("Scenarios"), flags=re.MULTILINE)[1:]:
        name, _, rest = block.partition("\n")
        run = re.search(r"^Run:\s*`([^`]+)`", rest, flags=re.MULTILINE)
        proves = re.search(r"^Proves:\s*(.+)$", rest, flags=re.MULTILINE)
        scenarios.append(
            Scenario(
                path.stem,
                name.strip(),
                run.group(1) if run else "",
                proves.group(1) if proves else "",
            )
        )
    return Recipe(path.stem, meta.get("kind", ""), scenarios, section("Gotchas"))


def segments(command: str) -> list[str]:
    """Split a shell line at top-level `&&` and `;`: outside quotes, `$(...)` and `{ ...; }`."""
    parts, current, depth, quote, i = [], [], 0, "", 0
    while i < len(command):
        c = command[i]
        if quote:
            quote = "" if c == quote else quote
        elif c in "'\"":
            quote = c
        elif c in "{(":
            depth += 1
        elif c in "})":
            depth -= 1
        elif depth == 0 and (command.startswith("&&", i) or c == ";"):
            parts.append("".join(current).strip())
            current = []
            i += 2 if c == "&" else 1
            continue
        current.append(c)
        i += 1
    parts.append("".join(current).strip())
    return [p for p in parts if p]


def is_prerequisite(segment: str) -> bool:
    """Whether a segment is one of the checks that exit 3 when a prerequisite is missing."""
    return PREREQUISITE.fullmatch(segment) is not None


def without_assignments(segment: str) -> tuple[dict[str, str], str]:
    """Split leading `NAME=value` assignments off a command."""
    env = {}
    while found := ASSIGNMENT.match(segment):
        env[found.group(1)] = shlex.split(found.group(2))[0]
        segment = segment[found.end() :]
    return env, segment


def matrix_pythons(job: dict) -> list[str]:
    """The Python versions a job's matrix runs, or none when it has no such matrix."""
    versions = ((job.get("strategy") or {}).get("matrix") or {}).get("python-version")
    return [str(v) for v in versions] if isinstance(versions, list) else []


def version_key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")
    return int(major), int(minor)


def listed(versions: set[str]) -> str:
    return ", ".join(sorted(versions, key=version_key)) or "none"


def condition_of(step: dict) -> str:
    """A step's `if:`, without the `${{ }}` GitHub allows around it."""
    condition = str(step.get("if", "")).strip()
    if condition.startswith("${{") and condition.endswith("}}"):
        condition = condition[3:-2].strip()
    return condition


def step_pythons(step: dict, versions: list[str]) -> set[str] | None:
    """The matrix versions a step runs on: all of them when its `if:` reads no matrix value, or
    None when it reads one in a form this does not read."""
    condition = condition_of(step)
    if not MATRIX_READ.search(condition):
        return set(versions)
    named = [PYTHON_IS.fullmatch(part) for part in re.split(r"\s*\|\|\s*", condition)]
    if all(named):
        return set(versions) & {found.group(1) for found in named}
    left_out = [PYTHON_IS_NOT.fullmatch(part) for part in re.split(r"\s*&&\s*", condition)]
    if all(left_out):
        return set(versions) - {found.group(1) for found in left_out}
    return None


def scenario_pythons(prerequisites: list[str], versions: list[str]) -> set[str]:
    """The matrix versions a scenario runs on: those its Python version tests let through."""
    runs = set(versions)
    for prerequisite in prerequisites:
        if found := VERSION_GUARD.match(prerequisite):
            # VERSION_TEST admits only a comparison of sys.version_info with tuples of integers,
            # and `info` is what sys.version_info is on that version's first release.
            test = found.group("test").replace("sys.version_info", "info")
            runs = {
                v
                for v in runs
                if not eval(test, {"__builtins__": {}}, {"info": (*version_key(v), 0, "final", 0)})  # noqa: S307
            }
    return runs


def step_commands(step: dict) -> tuple[list[str], list[str]]:
    """A step's commands, one per line, and the `sudo apt-get` lines the recipes check instead."""
    lines = re.sub(r"\\\n\s*", " ", step["run"]).splitlines()
    commands = [
        " ".join(line.split())
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    apt = [c for c in commands if c.startswith("sudo apt-get")]
    return [c for c in commands if c not in apt], apt


def runs_on_linux(step: dict) -> bool:
    """Whether a step runs on Linux, as far as its `if:` compares `runner.os`.

    GitHub compares strings without regard to case, so this does too. Comparisons joined by `||`
    need one to hold; otherwise every one must.
    """
    condition = condition_of(step)
    holds = [
        (value.casefold() == "linux") == (op == "==") for op, value in OS_TEST.findall(condition)
    ]
    if not holds:
        return True
    return any(holds) if "||" in condition else all(holds)


def check_suite(root: pathlib.Path, suite: Recipe) -> list[str]:
    problems = []
    jobs = yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
    steps = [(name, job, step) for name, job in jobs.items() for step in job.get("steps", [])]
    unmodelled = set()
    for job_name, job in jobs.items():
        odd = [v for v in matrix_pythons(job) if not MAJOR_MINOR.fullmatch(v)]
        if odd:
            unmodelled.add(job_name)
            problems.append(
                f"{WORKFLOW}: job '{job_name}' tests Pythons this check cannot compare: {odd}; "
                "it reads MAJOR.MINOR versions only"
            )
    named = set()
    for scenario in suite.scenarios:
        where = f"suite.md: scenario {scenario.name}"
        names = STEP_NAMED.findall(scenario.proves)
        if len(names) != 1:
            problems.append(
                f"{where}: its Proves line must name one workflow step as CI's *<name>* step"
            )
            continue
        named.add(names[0])
        candidates = [
            (job_name, job, s)
            for job_name, job, s in steps
            if s.get("name") == names[0] and "run" in s and runs_on_linux(s)
        ]
        if len(candidates) != 1:
            problems.append(
                f"{where}: {WORKFLOW} has {len(candidates)} Linux step(s) named '{names[0]}'"
            )
            continue
        job_name, job, step = candidates[0]
        commands, apt = step_commands(step)
        run = scenario.run
        if commands and "pytest" in commands[-1]:
            if not run.endswith(PYTEST_SUFFIX):
                problems.append(
                    f"{where}: Run line must end with the pytest exit-3 mapping '{PYTEST_SUFFIX}'"
                )
            run = run.removesuffix(PYTEST_SUFFIX)
        parts = segments(run)
        prerequisites = [p for p in parts if is_prerequisite(p)]
        ran, assigned = [], {}
        for part in (p for p in parts if not is_prerequisite(p)):
            env, command = without_assignments(part)
            assigned.update(env)
            ran.append(" ".join(command.split()))
        if ran != commands:
            problems.append(
                f"{where}: runs {ran} but step '{names[0]}' runs {commands} "
                "(apart from prerequisite checks and NAME=value prefixes)"
            )
        versions = matrix_pythons(job)
        if job_name in unmodelled:
            pass  # reported once for the job above
        elif versions:
            expected = step_pythons(step, versions)
            actual = scenario_pythons(prerequisites, versions)
            if expected is None:
                problems.append(
                    f"{where}: step '{names[0]}' has an if: condition this check cannot read: "
                    f"{step['if']!r}"
                )
            elif actual != expected:
                problems.append(
                    f"{where}: runs on Python {listed(actual)}, "
                    f"but step '{names[0]}' runs on {listed(expected)}"
                )
        elif any(VERSION_GUARD.match(p) for p in prerequisites):
            problems.append(
                f"{where}: checks the Python version, but step '{names[0]}' has no Python matrix"
            )
        if apt and not any(p.startswith("command -v ") for p in prerequisites):
            problems.append(
                f"{where}: step '{names[0]}' installs system packages ({apt}); "
                "check for them and exit 3 when they are missing"
            )
        step_env = {k: str(v) for k, v in (step.get("env") or {}).items()}
        for name, value in assigned.items():
            if step_env.get(name) != value:
                problems.append(
                    f"{where}: sets {name}={value!r}, but the step sets {step_env.get(name)!r}"
                )
        for name in step_env.keys() - assigned.keys():
            if not any(f"${name}" in p for p in prerequisites):
                problems.append(f"{where}: step '{names[0]}' sets {name}; set it or check for it")
    for _, _, step in steps:
        if "uv " in step.get("run", "") and step.get("name") not in named:
            problems.append(f"suite.md: no scenario runs {WORKFLOW} step '{step.get('name')}'")
    return problems


def pytest_paths(command: str) -> list[str]:
    words = shlex.split(command)
    paths, skip = [], False
    for word in words[words.index("pytest") + 1 :]:
        if skip:
            skip = False
        elif word in PYTEST_VALUE_OPTIONS:
            skip = True
        elif not word.startswith("-"):
            paths.append(word.split("::")[0].rstrip("/"))
    return paths


def check_areas(suite: Recipe, areas: list[Recipe]) -> tuple[list[str], int]:
    problems, matched = [], 0
    by_name = {s.name: s for s in suite.scenarios}
    main_sync = next((p for p in segments(by_name["main"].run) if not is_prerequisite(p)), "")
    for recipe in areas:
        claims: dict[str, re.Match] = {}
        for claim in CLAIM.finditer(recipe.gotchas):
            name = claim.group("scenario")
            if name is None:
                if len(recipe.scenarios) != 1:
                    problems.append(
                        f"{recipe.name}.md: says 'Its scenario' but has "
                        f"{len(recipe.scenarios)} scenarios; name the one it means"
                    )
                    continue
                name = recipe.scenarios[0].name
            claims[name] = claim
        for scenario in recipe.scenarios:
            where = f"{recipe.name}.md: scenario {scenario.name}"
            claim = claims.pop(scenario.name, None)
            if claim is None:
                problems.append(
                    f"{where}: its Gotchas must say it is a suite scenario word for word "
                    "or runs part of the suite's `main` scenario"
                )
                continue
            run = scenario.run
            if not run.endswith(PYTEST_SUFFIX):
                problems.append(
                    f"{where}: Run line must end with the pytest exit-3 mapping '{PYTEST_SUFFIX}'"
                )
            if claim.group("copy"):
                twin = by_name.get(claim.group("copy"))
                if twin is None:
                    problems.append(f"{where}: suite has no scenario '{claim.group('copy')}'")
                    continue
                if run != twin.run:
                    problems.append(
                        f"{where}: is not suite {twin.name} word for word:\n"
                        f"    here:  {run}\n    suite: {twin.run}"
                    )
                    continue
            else:
                commands = [
                    p for p in segments(run.removesuffix(PYTEST_SUFFIX)) if not is_prerequisite(p)
                ]
                if (
                    len(commands) != 2
                    or commands[0] != main_sync
                    or not commands[1].startswith("uv run pytest ")
                ):
                    problems.append(
                        f"{where}: must run suite main's `{main_sync}`, "
                        "then `uv run pytest <paths>`"
                    )
                    continue
                stray = [
                    p
                    for p in pytest_paths(commands[1])
                    if not p.startswith("tests/")
                    or p == "tests/integrations"
                    or p.startswith("tests/integrations/")
                ]
                if stray:
                    problems.append(f"{where}: runs {stray}, which suite main does not run")
                    continue
            matched += 1
        for name in claims:
            problems.append(
                f"{recipe.name}.md: its Gotchas name scenario '{name}', which it does not have"
            )
    return problems, matched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=pathlib.Path,
        default=pathlib.Path(__file__).resolve().parents[2],
        help="the repository to check (default: the one holding this script)",
    )
    parser.add_argument(
        "--pythons",
        action="store_true",
        help=f"print the Pythons job '{TEST_JOB}' of {WORKFLOW} lists, space-separated, and exit",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    if args.pythons:
        jobs = yaml.safe_load((root / WORKFLOW).read_text())["jobs"]
        versions = matrix_pythons(jobs.get(TEST_JOB) or {})
        if not versions:
            print(f"{WORKFLOW}: job '{TEST_JOB}' lists no python-version matrix", file=sys.stderr)
            return 1
        print(" ".join(versions))
        return 0
    recipes = [parse_recipe(p) for p in sorted((root / "verification/recipes").glob("*.md"))]
    suite = next(r for r in recipes if r.kind == "suite")
    areas = [r for r in recipes if r.kind in AREA_KINDS]
    problems = check_suite(root, suite)
    area_problems, matched = check_areas(suite, areas)
    problems += area_problems
    for problem in problems:
        print(problem)
    if problems:
        print(f"recipes-match-ci: {len(problems)} mismatch(es)")
        return 1
    print(
        f"recipes-match-ci: ok: {len(suite.scenarios)} suite scenarios run their {WORKFLOW} steps; "
        f"{matched} area scenarios in {len(areas)} recipes match the suite"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
