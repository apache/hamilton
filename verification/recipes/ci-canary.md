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
kind: ci
covers: .github/workflows/hamilton-main.yml, verification/scripts/ci_canary_rehearsal.py
---
# The daily canary and its Slack report

`hamilton-main.yml` also runs every day on `main`, testing it against the newest release of each dependency, because the repository commits no lockfile. When a job fails or hits its time limit, its `notify-slack` job posts the failed steps and a link to the run to the maintainers' Slack channel. Maintainers can also run the workflow by hand to send a test message. Each scenario but `real-listing` runs a scratch copy of the workflow under [act](https://nektosact.com). In the copy, the commands of every job but `notify-slack` are stubs, and a local stub stands in for the Slack webhook and GitHub's jobs application programming interface (API). The scenario checks that the jobs that ran are exactly the ones it expects, out of every job the workflow declares, and what was posted. `real-listing` runs the notify job's listing step on this machine over a real failed run's jobs.

## How a user reaches it

- The 04:17 Coordinated Universal Time (UTC) schedule, in apache/hamilton only; a fork's scheduled run skips every job.
- **Actions** > **Unit Tests** > **Run workflow** with *notify-slack* on, which posts a test message whatever the outcome.
- Pull-request runs, and manual runs with *notify-slack* off, which test like the daily run and post nothing.

## Scenarios

### schedule-failure
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" schedule-failure`
Proves: a scheduled run in apache/hamilton runs every job, and when its test step fails posts once, naming each failed job and step on its own line, with a link to the run.

### schedule-pass
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" schedule-pass`
Proves: a scheduled run that passes runs every job but the notify job, skips the notify job, and posts nothing.

### schedule-fork
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" schedule-fork`
Proves: a fork's scheduled run skips every job the workflow declares, so it neither tests nor posts; a job added without the fork guard fails it.

### dispatch-test-post
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" dispatch-test-post`
Proves: a manual run with *notify-slack* on tests and posts once, saying it tests the notification path and giving the run's outcome.

### dispatch-test-post-failure
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" dispatch-test-post-failure`
Proves: a failing manual run with *notify-slack* on runs every job and posts once, saying it tests the notification path from a run which failed, naming each failed job and step on its own line, with a link to the run.

### dispatch-quiet
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" dispatch-quiet`
Proves: a failing manual run with *notify-slack* off tests and posts nothing.

### dispatch-fork
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" dispatch-fork`
Proves: a fork's manual run with *notify-slack* on still tests, and posts nothing, because only apache/hamilton holds the webhook.

### pull-request
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" pull-request`
Proves: a failing pull-request run tests and posts nothing.

### listing-unavailable
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" listing-unavailable`
Proves: when the jobs API fails, a failing scheduled run still posts once, saying the failed steps are unavailable and linking the run.

### timeout
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" timeout`
Proves: a scheduled run whose test job hangs until its time limit posts once, naming each timed-out job and its step.

### real-listing
Run: `uv run --script verification/scripts/ci_canary_rehearsal.py "${CI_CANARY_WORKFLOW:-.github/workflows/hamilton-main.yml}" real-listing`
Proves: the notify job's listing step, run unchanged over a real failed apache/hamilton run's jobs, lists exactly the failed job and step pairs and no passing step.

## Gotchas

- Set `CI_CANARY_WORKFLOW` to the workflow file to rehearse, such as another worktree's `.github/workflows/hamilton-main.yml`; it defaults to this checkout's. A file with no `notify-slack` job fails every scenario.
- Every scenario but `real-listing` needs a Linux host, Docker, act (on `PATH`, or named by `ACT`; checked with act 0.2.92), and the GitHub command-line interface (CLI), `gh`; `real-listing` needs `gh` and `jq`. A scenario exits 3 when one is missing. The `Run:` lines start the script with uv. act's runner image (`catthehacker/ubuntu:act-latest`, or `CI_CANARY_IMAGE`) has no GitHub CLI, so the host's `gh` binary is mounted into it, and it must be a Linux build.
- Needs network: act pulls the runner image, the script fetches the Slack action at the commit the workflow pins (without credentials, and hands it to act with `--local-repository`), and `real-listing` reads one run's jobs from api.github.com without credentials.
- A scenario also exits 3, with a one-line reason, when the machine rather than the workflow is at fault. That happens when the action's fetch cannot reach GitHub, or when act cannot pull the runner image or reach the Docker daemon. It also happens when api.github.com is unreachable or answers 403, 429, or 5xx; an unauthenticated read is rate-limited to 60 requests an hour. A job that fails for any other reason stays a failure.
- The scratch copy of the workflow and the fetched action go in a temporary directory (`TMPDIR`, else `/tmp`). When that is full, the fetch fails and the scenario stops with git's own error; point `TMPDIR` at a disk with room.
- Nothing reaches Slack or writes to GitHub. The webhook and the jobs API the notify job calls are a local stub on 127.0.0.1, which act's containers reach through `--network host`. The stub answers 200 `ok`, as Slack does, because any other answer makes the Slack action retry and post again.
- act has no jobs API, so each scenario's jobs-API response is built from the outcome it stubbed, in GitHub's field names. `real-listing` is where the listing filter meets GitHub's real output. It uses run 41606806942, or the newest failed run of the workflow after that one has expired.
- act always runs attempt 1, so the re-run guard (`github.run_attempt == 1`) is checked by reading the notify job's `if:`, not here.
- act ignores a job's `timeout-minutes` but enforces a step's, and a job it times out ends `failure`, where GitHub ends it `cancelled`. So `timeout` also puts the one-minute limit on the hanging step, and proves a hung test is reported through the notify job's `failure` branch; its `cancelled` branch is checked by reading the `if:`.
- Each scenario expects a set of jobs relative to the workflow's `jobs` (every job, every job but `notify-slack`, or none) and fails unless the jobs that ran are exactly that set, so a new job is judged without editing the script. Every job the workflow declares must be planned for the event (`act --list`), and a skip counts only when act exited 0, so an act run that did nothing never passes as every job skipped.
- A post's lines between its header and the run link must match the expected listing exactly, in order: each failed job and step, the unavailable notice, or nothing for a passing run.
- `timeout` lasts just over a minute, the shortest time limit a step takes. The other act scenarios take about 10 to 15 seconds each, most of it starting containers.
