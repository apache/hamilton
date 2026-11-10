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
# requires-python = ">=3.10"
# dependencies = ["ruamel.yaml>=0.18"]
# ///
"""Rehearse the scheduled canary and Slack notify job of hamilton-main.yml under `act`.

Each act scenario runs a scratch copy of the workflow under nektos/act: every job but the notify
job has its steps replaced by `exit 0` / `exit 1` / `sleep` stubs and its services dropped, and the
notify job's `API_URL` points at a local stub that serves a jobs-API response shaped like the
scenario's outcome. `SLACK_WEBHOOK_URL` points at the same stub, which records every post. The run's
repository comes from the scratch repository's `origin` remote. A scenario passes when the set of
jobs that ran is exactly the one it expects, out of every job the workflow declares, and the
requests the stub received match what a maintainer or a fork owner should see. `real-listing`
instead runs the notify job's listing step on this machine over a real failed run's jobs.

Usage: ci_canary_rehearsal.py WORKFLOW SCENARIO

Exit codes: 0 passed, 1 a mismatch or error, 2 usage, 3 unreachable here: a prerequisite is
missing, the host is not Linux, or the network, a registry, or the Docker daemon failed.
Set ACT to the act binary when it is not on PATH, and CI_CANARY_IMAGE to the runner image
(default catthehacker/ubuntu:act-latest).
"""

from __future__ import annotations

import difflib
import enum
import io
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ruamel.yaml import YAML

# Names this script relies on in the workflow; `checked` says which one is missing when a change
# to the workflow renames it.
UPSTREAM = "apache/hamilton"
FORK = "example-fork/hamilton"
TEST_JOB = "test"
NOTIFY_JOB = "notify-slack"
LISTING_STEP_ID = "message"
FAILING_STEP = "Test pyspark"  # the step a failing scenario stubs to fail, on every matrix leg
SETUP_STEP = "Set up job"  # the step GitHub and act put first in every job
REAL_RUN_ID = "41606806942"  # a failed hamilton-main.yml run; the newest failed one if it expired
IMAGE = os.environ.get("CI_CANARY_IMAGE", "catthehacker/ubuntu:act-latest")
SCHEDULED_HEADER = "Hamilton latest-dependency CI failed:"
TEST_HEADER = "Test of Hamilton's CI Slack notification path"
UNAVAILABLE = "(failed steps unavailable)"
RUN_LINK = f"/{UPSTREAM}/actions/runs/"

# What act or git prints when the machine, not the workflow, is at fault.
DOCKER_ERRORS = (
    "Error response from daemon",  # a refused, rate-limited or unreachable image pull
    "Cannot connect to the Docker daemon",
    "error during connect",
)
GIT_NETWORK_ERRORS = (
    "unable to access",  # git's prefix for every transport failure over HTTPS
    "Could not resolve host",
    "Failed to connect",
    "timed out",
    "Connection reset",
    "early EOF",
)


class Unreachable(Exception):
    """A prerequisite or the environment is missing: the scenario cannot run here (exit 3)."""


class Mismatch(Exception):
    """The workflow lacks a name this script relies on (exit 1)."""


class SetupFailed(Exception):
    """A tool preparing the rehearsal failed; its message carries the tool's own error (exit 1)."""


class Ran(enum.Enum):
    """Which of the workflow's jobs a scenario expects to run; every other job must be skipped.

    Relative to the jobs the workflow declares, so a new job is judged in every scenario: it
    must run wherever every job runs, and an unguarded one fails `schedule-fork`.
    """

    EVERY_JOB = "every job"
    ALL_BUT_NOTIFY = f"every job but {NOTIFY_JOB}"
    NO_JOB = "no job"

    def of(self, universe: set[str]) -> set[str]:
        if self is Ran.EVERY_JOB:
            return set(universe)
        if self is Ran.ALL_BUT_NOTIFY:
            return universe - {NOTIFY_JOB}
        return set()


@dataclass
class Scenario:
    event: str
    repository: str
    outcome: str  # "pass", "fail" (FAILING_STEP exits 1) or "timeout" (FAILING_STEP sleeps)
    ran: Ran
    notify_input: bool | None = None  # the workflow_dispatch input, None for other events
    api_fails: bool = False
    posts: int = 0
    text_starts: str = ""
    text_has: tuple[str, ...] = ()
    lists_failed_steps: bool = False  # the post names each failed job and step on its own line


SCENARIOS: dict[str, Scenario] = {
    # A dependency breaks a step: one post naming each failed job and step, with the run link.
    "schedule-failure": Scenario(
        "schedule", UPSTREAM, "fail", ran=Ran.EVERY_JOB, posts=1, text_starts=SCHEDULED_HEADER,
        text_has=(RUN_LINK,), lists_failed_steps=True,
    ),
    # Everything passes: the notify job is skipped.
    "schedule-pass": Scenario("schedule", UPSTREAM, "pass", ran=Ran.ALL_BUT_NOTIFY),
    # A fork's daily run: nothing runs at all, even with a step that would fail.
    "schedule-fork": Scenario("schedule", FORK, "fail", ran=Ran.NO_JOB),
    # A maintainer's test post: says it is a test and gives the outcome.
    "dispatch-test-post": Scenario(
        "workflow_dispatch", UPSTREAM, "pass", notify_input=True, ran=Ran.EVERY_JOB, posts=1,
        text_starts=TEST_HEADER, text_has=("which passed", RUN_LINK),
    ),
    # A maintainer's test post from a failing run: says it failed and names what broke.
    "dispatch-test-post-failure": Scenario(
        "workflow_dispatch", UPSTREAM, "fail", notify_input=True, ran=Ran.EVERY_JOB, posts=1,
        text_starts=TEST_HEADER, text_has=("which failed", RUN_LINK), lists_failed_steps=True,
    ),
    # A manual run without the switch stays quiet even when it fails.
    "dispatch-quiet": Scenario(
        "workflow_dispatch", UPSTREAM, "fail", notify_input=False, ran=Ran.ALL_BUT_NOTIFY,
    ),
    # A fork owner trying the switch: the fork has no webhook, so nothing posts.
    "dispatch-fork": Scenario(
        "workflow_dispatch", FORK, "pass", notify_input=True, ran=Ran.ALL_BUT_NOTIFY,
    ),
    # A pull request tests, and stays quiet when it fails.
    "pull-request": Scenario("pull_request", UPSTREAM, "fail", ran=Ran.ALL_BUT_NOTIFY),
    # The jobs API is down: the post still goes out, with the run link.
    "listing-unavailable": Scenario(
        "schedule", UPSTREAM, "fail", api_fails=True, ran=Ran.EVERY_JOB, posts=1,
        text_starts=SCHEDULED_HEADER, text_has=(UNAVAILABLE, RUN_LINK),
    ),
    # A dependency hangs a test until the job's time limit: still reported.
    "timeout": Scenario(
        "schedule", UPSTREAM, "timeout", ran=Ran.EVERY_JOB, posts=1,
        text_starts=SCHEDULED_HEADER, lists_failed_steps=True,
    ),
}  # fmt: skip


# ---------------------------------------------------------------------------------------------
# The workflow, read once per scenario.


def load(path: Path):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    return yaml, yaml.load(path.read_text())


def dump(yaml: YAML, workflow) -> str:
    out = io.StringIO()
    yaml.dump(workflow, out)
    return out.getvalue()


def checked(workflow, path: Path):
    """The listing step and the Slack action's `owner/repo@sha`, after checking every name."""
    jobs = workflow.get("jobs") or {}
    for job_id in (TEST_JOB, NOTIFY_JOB):
        if job_id not in jobs:
            raise Mismatch(f"{path} has no `{job_id}` job; the rehearsal needs the canary's jobs")
    if not any(s.get("name") == FAILING_STEP for s in jobs[TEST_JOB].get("steps", [])):
        raise Mismatch(f"no `{TEST_JOB}` step is named {FAILING_STEP!r}; update FAILING_STEP")
    steps = jobs[NOTIFY_JOB]["steps"]
    listing = next((s for s in steps if s.get("id") == LISTING_STEP_ID), None)
    if listing is None or "API_URL" not in listing.get("env", {}):
        raise Mismatch(f"no `{NOTIFY_JOB}` step has id {LISTING_STEP_ID!r} and an API_URL env")
    actions = [s["uses"] for s in steps if "uses" in s]
    if len(actions) != 1:
        raise Mismatch(f"`{NOTIFY_JOB}` should use exactly one action, found {actions}")
    return listing, actions[0]


def job_ids(workflow) -> set[str]:
    """Every job the workflow declares: the universe each scenario's expectation is drawn from."""
    return set(workflow["jobs"])


def stubbed_jobs(workflow) -> list[str]:
    """The jobs whose steps the rehearsal replaces: all but the notify job, in workflow order."""
    return [job_id for job_id in workflow["jobs"] if job_id != NOTIFY_JOB]


def job_names(workflow, job_id: str) -> list[str]:
    """The names GitHub gives a job's runs: its `name` (else its id), with each matrix leg's values."""
    job = workflow["jobs"][job_id]
    name = job.get("name", job_id)
    matrix = {
        k: v for k, v in job.get("strategy", {}).get("matrix", {}).items() if isinstance(v, list)
    }
    legs = itertools.product(*matrix.values())
    return [f"{name} ({', '.join(map(str, leg))})" if matrix else name for leg in legs]


def failed_lines(workflow) -> list[str]:
    return [f"{name}: {FAILING_STEP}" for name in job_names(workflow, TEST_JOB)]


def expected_listing(workflow, scenario: Scenario) -> list[str]:
    """The lines a post carries between its header and the run link."""
    if scenario.lists_failed_steps:
        return failed_lines(workflow)
    return [UNAVAILABLE] if scenario.api_fails else []


def jobs_response(workflow, scenario: Scenario) -> dict:
    """A jobs-API response shaped like this scenario's outcome, in GitHub's field names."""
    jobs = []
    for job_id in stubbed_jobs(workflow):
        names = [s.get("name", "") for s in workflow["jobs"][job_id].get("steps", [])]
        steps = [SETUP_STEP, *names]
        broken = scenario.outcome != "pass" and job_id == TEST_JOB
        ended = {"fail": "failure", "timeout": "cancelled"}.get(scenario.outcome, "success")
        conclusions, after = [], False  # steps after the broken one are skipped
        for step in steps:
            hit = broken and step == FAILING_STEP and not after
            conclusions.append(ended if hit else "skipped" if after else "success")
            after = after or hit
        for name in job_names(workflow, job_id):
            jobs.append(
                {
                    "name": name,
                    "status": "completed",
                    "conclusion": ended if broken else "success",
                    "steps": [
                        {"name": s, "status": "completed", "conclusion": c, "number": i}
                        for i, (s, c) in enumerate(zip(steps, conclusions, strict=True), 1)
                    ],
                }
            )
    notify = workflow["jobs"][NOTIFY_JOB].get("name", NOTIFY_JOB)
    jobs.append({"name": notify, "status": "in_progress", "conclusion": None, "steps": []})
    return {"total_count": len(jobs), "jobs": jobs}


def stub_job(job, job_id: str, scenario: Scenario) -> None:
    """Replace a job's work with `exit 0`, or with the scenario's outcome on FAILING_STEP."""
    job.pop("services", None)
    job.pop("container", None)
    if "uses" in job:  # a reusable workflow: one passing step in its place
        for key in ("uses", "with", "secrets"):
            job.pop(key, None)
        job["runs-on"] = "ubuntu-latest"
        job["steps"] = [{"run": "exit 0"}]
        return
    stub = {"pass": "exit 0", "fail": "exit 1", "timeout": "sleep 600"}[scenario.outcome]
    for step in job.get("steps", []):
        for key in ("uses", "with", "shell"):
            step.pop(key, None)
        hit = job_id == TEST_JOB and step.get("name") == FAILING_STEP
        step["run"] = stub if hit else "exit 0"
        if hit and scenario.outcome == "timeout":
            # act ignores a job's time limit but enforces a step's, ending the job `failure`
            # where GitHub ends it `cancelled`
            step["timeout-minutes"] = 1
    if job_id == TEST_JOB and scenario.outcome == "timeout":
        job["timeout-minutes"] = 1


def scratch_copy(path: Path, scenario: Scenario, api_url: str) -> tuple[str, str]:
    """The scenario's workflow text, and its unified diff against the branch file.

    The diff compares both files after the same YAML dump, which re-indents lists, so only
    differences in content show.
    """
    yaml, workflow = load(path)
    original = dump(yaml, workflow)
    listing, _ = checked(workflow, path)
    for job_id in stubbed_jobs(workflow):
        stub_job(workflow["jobs"][job_id], job_id, scenario)
    listing["env"]["API_URL"] = api_url
    text = dump(yaml, workflow)
    lines = difflib.unified_diff(
        original.splitlines(keepends=True), text.splitlines(keepends=True), "branch", "scratch", n=0
    )
    return text, "".join(lines)


# ---------------------------------------------------------------------------------------------
# The local stub: the jobs API and the webhook, recording every request.


class Stub:
    def __init__(self, jobs: dict | None):
        self.requests: list[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _reply(self, code: int, body: bytes, kind: str) -> None:
                self.send_response(code)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802 - the http.server hook name
                stub.requests.append({"method": "GET", "path": self.path})
                if jobs is not None and "/actions/runs/" in self.path and "/jobs" in self.path:
                    self._reply(200, json.dumps(jobs).encode(), "application/json")
                else:
                    self._reply(503, b'{"message": "stub: jobs API down"}', "application/json")

            def do_POST(self) -> None:  # noqa: N802 - the http.server hook name
                body = self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode()
                stub.requests.append({"method": "POST", "path": self.path, "body": body})
                # Slack's answer: anything else makes the action retry and post again
                self._reply(200, b"ok", "text/plain")

            def log_message(self, *args) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def posts(self) -> list[dict]:
        return [r for r in self.requests if r["method"] == "POST"]

    def close(self) -> None:
        self.server.shutdown()


# ---------------------------------------------------------------------------------------------
# Running act and reading what happened.


def require(tool: str, why: str) -> str:
    path = shutil.which(tool)
    if not path:
        raise Unreachable(f"needs {tool}: {why}")
    return path


def last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "(no output)"


def git(cwd: Path, *args: str, network: bool = False) -> None:
    """Run git; with `network`, a transport failure is the machine's, so it is Unreachable."""
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    result = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True)
    if not result.returncode:
        return
    if network and any(marker in result.stderr for marker in GIT_NETWORK_ERRORS):
        raise Unreachable(f"git {args[0]} needs network: {last_line(result.stderr)}")
    raise SetupFailed(f"git {' '.join(args)} exited {result.returncode}: {result.stderr.strip()}")


def fetch_action(uses: str, dest: Path) -> None:
    """Fetch the pinned action without credentials, so act never clones it with the stub token."""
    repo, sha = uses.split("@", 1)
    dest.mkdir()
    git(dest, "init", "--quiet")
    git(dest, "fetch", "--quiet", "--depth", "1", f"https://github.com/{repo}", sha, network=True)
    git(dest, "checkout", "--quiet", "FETCH_HEAD")


def scratch_repository(root: Path, repository: str, workflow_text: str) -> Path:
    workdir = root / "repo"
    (workdir / ".github/workflows").mkdir(parents=True)
    (workdir / ".github/workflows/hamilton-main.yml").write_text(workflow_text)
    git(workdir, "init", "--quiet", "--initial-branch", "main")
    git(workdir, "remote", "add", "origin", f"https://github.com/{repository}.git")
    git(workdir, "add", ".")
    git(workdir, "-c", "user.name=rehearsal", "-c", "user.email=rehearsal@invalid", "commit",
        "--quiet", "-m", "rehearsal")  # fmt: skip
    return workdir


def docker_failure(entries: list[dict], stderr: str) -> str | None:
    """The Docker error that kept act's jobs from starting, if one did.

    Only errors raised while setting a job up, or by act itself, count: a workflow step's failure
    never carries the Docker daemon's wording, so a genuine mismatch is never taken for one.
    """
    setup_errors = [
        str(entry.get("msg", ""))
        for entry in entries
        if entry.get("level") == "error" and "--setup-job" in (entry.get("stepid") or [])
    ]
    act_errors = [line for line in stderr.splitlines() if line.startswith("Error:")]
    for message in (*setup_errors, *act_errors):
        if any(marker in message for marker in DOCKER_ERRORS):
            return message.strip()
    return None


def run_act(root: Path, workdir: Path, universe: set[str], scenario: Scenario, uses: str,
            webhook: str):  # fmt: skip
    """Each job's results, the jobs act planned for the event, act's exit code, and its log."""
    act = require(os.environ.get("ACT", "act"), "install nektos/act or set ACT to its binary")
    gh = require("gh", "act's runner image has no GitHub CLI, so the host's gh is mounted into it")
    require("docker", "act runs every job in a Docker container")
    if subprocess.run(["docker", "info"], capture_output=True).returncode != 0:
        raise Unreachable("needs a running Docker daemon for act")
    action = root / "action"
    fetch_action(uses, action)
    event = {}
    if scenario.event == "workflow_dispatch":
        # GitHub's event payload carries inputs as strings; act types them from there
        event["inputs"] = {"notify-slack": str(scenario.notify_input).lower()}
    if scenario.event == "pull_request":
        event["pull_request"] = {"head": {"ref": "rehearsal"}, "base": {"ref": "main"}}
    (root / "event.json").write_text(json.dumps(event))
    common = [
        scenario.event,
        "--workflows",
        ".github/workflows",
        "--eventpath",
        str(root / "event.json"),
    ]
    listed = subprocess.run([act, *common, "--list"], cwd=workdir, capture_output=True, text=True)
    if listed.returncode:
        raise SetupFailed(f"act --list exited {listed.returncode}: {listed.stderr.strip()}")
    # `act --list` prints a header, then one row per job: stage, job id, name, ...
    planned = {
        columns[1]
        for columns in (line.split() for line in listed.stdout.splitlines()[1:])
        if len(columns) > 1 and columns[1] in universe
    }
    command = [
        act, *common,
        "--platform", f"ubuntu-latest={IMAGE}",
        "--secret", f"SLACK_WEBHOOK_URL={webhook}",
        # gh refuses to run without a token; only the local stub ever receives this one
        "--secret", "GITHUB_TOKEN=rehearsal-stub-token",
        "--local-repository", f"{uses}={action}",
        "--container-options", f"-v {gh}:/usr/local/bin/gh:ro",
        "--rm",
        "--json",
    ]  # fmt: skip
    proc = subprocess.run(command, cwd=workdir, capture_output=True, text=True)
    entries = []
    for line in proc.stdout.splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    if proc.returncode and (failure := docker_failure(entries, proc.stderr)):
        raise Unreachable(f"act could not start its containers: {failure}")
    results: dict[str, list[str]] = {}
    for entry in entries:
        if entry.get("jobResult"):
            results.setdefault(entry.get("jobID", "?"), []).append(entry["jobResult"])
    return results, planned, proc.returncode, listed.stdout + proc.stdout + proc.stderr


def rehearse(path: Path, name: str) -> list[str]:
    if sys.platform != "linux":
        # act's runner image is a Linux container, the host's gh is mounted into it, and the
        # workflow's `runs-on: ubuntu-latest` steps assume a Linux runner
        raise Unreachable(f"act scenarios run only on a Linux host, not {sys.platform}")
    scenario = SCENARIOS[name]
    _, workflow = load(path)
    _, uses = checked(workflow, path)
    universe = job_ids(workflow)
    expected = scenario.ran.of(universe)
    stub = Stub(None if scenario.api_fails else jobs_response(workflow, scenario))
    problems: list[str] = []
    try:
        text, diff = scratch_copy(path, scenario, stub.url)
        switch = "" if scenario.notify_input is None else f", notify-slack={scenario.notify_input}"
        down = ", jobs API down" if scenario.api_fails else ""
        print(
            f"== {name}: {scenario.event} in {scenario.repository}, steps {scenario.outcome}{switch}{down}"
        )
        print(f"-- expects {scenario.ran.value} of {sorted(universe)} to run: {sorted(expected)}")
        print("-- scratch copy against the branch file, both through one YAML dump:")
        print(diff)
        with tempfile.TemporaryDirectory(prefix="ci-canary-") as tmp:
            root = Path(tmp)
            workdir = scratch_repository(root, scenario.repository, text)
            results, planned, code, log = run_act(
                root, workdir, universe, scenario, uses, f"{stub.url}/webhook"
            )
        ran = set(results)
        print(f"-- act planned {sorted(planned)} for {scenario.event} and exited {code}")
        print("-- jobs that ran, with each matrix leg's result:")
        for job_id in sorted(universe | ran):
            print(f"   {job_id}: {', '.join(results.get(job_id, [])) or 'skipped (did not run)'}")
        print(f"-- requests the stub received ({len(stub.requests)}):")
        for request in stub.requests:
            body = f"\n     body: {request['body']}" if "body" in request else ""
            print(f"   {request['method']} {request['path']}{body}")

        # A skip counts only when act planned the job and finished cleanly; otherwise an act that
        # did nothing would look like every job skipped by its `if:`.
        if missing := sorted(universe - planned):
            problems.append(f"act did not plan {missing} for {scenario.event}")
        expect_clean = scenario.outcome == "pass" or TEST_JOB not in expected
        if expect_clean and code != 0:
            problems.append(f"act exited {code} where no job should fail")
        problems += [f"{job} should have run but did not" for job in sorted(expected - ran)]
        problems += [f"{job} should have been skipped but ran" for job in sorted(ran - expected)]
        posts = stub.posts()
        if len(posts) != scenario.posts:
            problems.append(f"expected {scenario.posts} webhook post(s), got {len(posts)}")
        for post in posts[:1]:
            try:
                message = json.loads(post["body"])["text"]
            except (json.JSONDecodeError, KeyError, TypeError):
                problems.append(
                    f"the post is not a JSON object with a text field: {post['body']!r}"
                )
                continue
            print(
                "-- the posted text:\n" + "\n".join(f"   | {line}" for line in message.splitlines())
            )
            if not message.startswith(scenario.text_starts):
                problems.append(f"the text does not start {scenario.text_starts!r}")
            problems += [
                f"the text lacks {part!r}" for part in scenario.text_has if part not in message
            ]
            # the lines between the header and the run link, in order, and nothing else
            listed = message.splitlines()[1:-1]
            if listed != (wanted := expected_listing(workflow, scenario)):
                problems.append(f"the text lists {listed}, expected exactly {wanted}")
        if problems:
            print("-- act's log, for locating the mismatch:")
            print(log[-20000:])
    finally:
        stub.close()
    return problems


# ---------------------------------------------------------------------------------------------
# The listing step against a real failed run.


def github_get(url: str) -> dict:
    """An unauthenticated GET: the repository is public, so no credential is sent anywhere.

    A 404 is the caller's to judge; a rate limit or a network failure is Unreachable.
    """
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code in (403, 429):
            remaining = error.headers.get("X-RateLimit-Remaining", "?")
            reset = error.headers.get("X-RateLimit-Reset", "?")
            raise Unreachable(
                f"api.github.com answered {error.code} (rate limit: {remaining} left, resets at"
                f" epoch {reset}) for {url}"
            ) from error
        if error.code >= 500:
            raise Unreachable(f"api.github.com answered {error.code} for {url}") from error
        raise
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        reason = getattr(error, "reason", error)
        raise Unreachable(f"cannot reach api.github.com: {reason}") from error


def real_listing(path: Path) -> list[str]:
    require("gh", "the listing step runs the GitHub CLI")
    require("jq", "the listing step builds the Slack payload with jq")
    _, workflow = load(path)
    listing, _ = checked(workflow, path)
    api = f"https://api.github.com/repos/{UPSTREAM}/actions"
    run_id = REAL_RUN_ID
    try:
        recorded = github_get(f"{api}/runs/{run_id}/jobs?per_page=100")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        query = "workflows/hamilton-main.yml/runs?status=failure&per_page=1"
        runs = github_get(f"{api}/{query}")["workflow_runs"]
        if not runs:
            raise Unreachable("no failed hamilton-main.yml run is left to list") from error
        run_id = str(runs[0]["id"])
        recorded = github_get(f"{api}/runs/{run_id}/jobs?per_page=100")
    broken = ("failure", "cancelled", "timed_out")
    expected = []
    for job in recorded["jobs"]:
        if job["conclusion"] in broken:
            steps = [s["name"] for s in job.get("steps", []) if s["conclusion"] in broken]
            expected += [f"{job['name']}: {s}" for s in steps] or [job["name"]]
    passing = {
        f"{j['name']}: {s['name']}"
        for j in recorded["jobs"]
        for s in j.get("steps", [])
        if s["conclusion"] == "success"
    }

    stub = Stub(recorded)
    try:
        with tempfile.TemporaryDirectory(prefix="ci-canary-") as tmp:
            output = Path(tmp) / "output"
            output.touch()
            env = {
                "PATH": os.environ["PATH"],
                "HOME": tmp,
                "GH_CONFIG_DIR": tmp,  # no stored login is read
                "GH_TOKEN": "rehearsal-stub-token",  # only the local stub receives it
                "API_URL": stub.url,
                "REPO": UPSTREAM,
                "RUN_ID": run_id,
                "RUN_URL": f"https://github.com/{UPSTREAM}/actions/runs/{run_id}",
                "EVENT": "schedule",
                "OUTCOME": "failed",
                "GITHUB_OUTPUT": str(output),
            }
            cmd = ["bash", "-e", "-c", listing["run"]]
            proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
            payload = output.read_text()
    finally:
        stub.close()
    print(f"== real-listing: the listing step, unchanged, over run {run_id}'s jobs")
    print(f"   (read without credentials from {api}/runs/{run_id}/jobs, served by a local stub)")
    print(f"-- step exit {proc.returncode}; stderr: {proc.stderr.strip() or '(none)'}")
    if proc.returncode != 0 or not payload.startswith("payload="):
        return [f"the step failed or wrote no payload: {payload!r}"]
    text = json.loads(payload.removeprefix("payload="))["text"]
    print("-- the composed text:\n" + "\n".join(f"   | {line}" for line in text.splitlines()))
    problems = []
    listed = text.splitlines()[1:-1]
    if listed != expected:
        problems.append(f"listed {listed}, expected the failed steps {expected}")
    if leaked := sorted(set(listed) & passing):
        problems.append(f"passing steps listed: {leaked}")
    if not expected:
        problems.append(f"run {run_id} has no failed step, so it proves nothing")
    return problems


def main(argv: list[str]) -> int:
    names = [*SCENARIOS, "real-listing"]
    if len(argv) != 2 or argv[1] not in names:
        usage = f"usage: {Path(sys.argv[0]).name} WORKFLOW {{{','.join(names)}}}"
        print(__doc__.split("\n\n")[0] + "\n\n" + usage, file=sys.stderr)
        return 2
    path = Path(argv[0])
    if not path.is_file():
        print(f"no workflow file at {path}", file=sys.stderr)
        return 2
    try:
        problems = real_listing(path) if argv[1] == "real-listing" else rehearse(path, argv[1])
    except Unreachable as missing:
        print(f"unreachable: {missing}", file=sys.stderr)
        return 3
    except Mismatch as mismatch:
        problems = [str(mismatch)]
    except SetupFailed as failed:
        print(f"error: {failed}", file=sys.stderr)
        return 1
    if problems:
        print("FAILED:\n" + "\n".join(f"  - {p}" for p in problems))
        return 1
    print("passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
