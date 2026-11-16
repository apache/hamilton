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
# 2611-09. Released Hamilton artifacts do not phone home

**Status:** Reconstructed from codebase (decided 2026-03 in [apache/hamilton#1512](https://github.com/apache/hamilton/pull/1512) / commit [45673b02](https://github.com/apache/hamilton/commit/45673b020f84f23eb982d0a563fe057cd971aeab), released in 1.90.0)

## Context

Opt-out usage telemetry was added in 2022-12 (commit [0dcd52a7](https://github.com/apache/hamilton/commit/0dcd52a71c32c3b4b43245c2603efa93b645ae29)). By default, the library sent anonymous usage events to PostHog when a Driver was created and when `execute()` finished. The events covered the operating system and Python version, a persistent universally unique identifier (UUID) kept in `~/.hamilton.conf`, Hamilton-only stack traces, and the decorators, adapters, and result builders in use. Users could turn it off with `telemetry.disable_telemetry()`, the `telemetry_enabled` key in `~/.hamilton.conf`, or `HAMILTON_TELEMETRY_ENABLED=false`. The message for [0dcd52a7](https://github.com/apache/hamilton/commit/0dcd52a71c32c3b4b43245c2603efa93b645ae29) gives the purpose, "to help us improve Hamilton and know where to apply development efforts", and the promise: "No user data or potentially sensitive information is or ever will be collected."

After the project entered the incubator of the Apache Software Foundation (ASF), #1512 gave the reason for removing it: "ASF policy does not permit phone-home telemetry in released artifacts." The pull request links no policy text, and no discussion of the removal on the project's mailing lists was found. It was opened and merged on 2026-03-08 by Stefan Krawczyk, approved by mentor Jarek Potiuk and by Dev-iL after a review that asked for deprecation ([review](https://github.com/apache/hamilton/pull/1512#pullrequestreview-3911170080)). The 1.90.0 release vote listed "Remove usage telemetry (PostHog) (#1512)" and passed the project's vote ([thread](https://lists.apache.org/thread/flo5w8347vr2yo7c4ssv1ndyd2c47dg2)) and the Incubator's ([thread](https://lists.apache.org/thread/po2w9xsbxj2d0j99fhml0spg7kh919tm)) with no comment on the change.

This record was reconstructed from pull request [apache/hamilton#1512](https://github.com/apache/hamilton/pull/1512) (body and reviews), commit [0dcd52a7](https://github.com/apache/hamilton/commit/0dcd52a71c32c3b4b43245c2603efa93b645ae29), [`hamilton/telemetry.py`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/telemetry.py#L29-L50), and the 1.90.0 release-vote threads.

## Decision

- All PostHog event tracking is removed from the library, the command-line interface (CLI), the experiments server, `contrib`, dataflows, and the user interface (UI) backend's tracking-server app ([45673b02](https://github.com/apache/hamilton/commit/45673b020f84f23eb982d0a563fe057cd971aeab) touches 25 files).
- [`hamilton/telemetry.py`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/telemetry.py#L29-L50) remains as a no-op stub, so existing calls to `telemetry.disable_telemetry()` keep working. `is_telemetry_enabled()` always returns `False`.
- The review on #1512 asked to "mark these methods as deprecated (via decorator, or raising a warning), and remove all traces in an upcoming major release", so both stub functions use `@deprecated(warn_starting=(1, 89, 0), fail_starting=(2, 0, 0))` (see 2611-04).

## Consequences

- No feature may add phone-home telemetry to a released artifact, as #1512 states the policy. The project loses the usage data it once used to decide where to apply development effort.
- The stub first shipped in 1.90.0; 1.89.0 still sent telemetry. Its `warn_starting` of 1.89.0 has passed, so calling it warns: through a logged warning in 1.90.0, and through a `FutureWarning` from the first release that carries [#1804](https://github.com/apache/hamilton/pull/1804) (see 2611-04). It raises `DeprecationError` from 2.0.0 on.
- The stub keeps only the two public functions, so code that imported anything else from `hamilton.telemetry` broke: `hamilton ui` failed with "cannot import name 'API_KEY' from 'hamilton.telemetry'" until the UI package was fixed in its next release ([#1649](https://github.com/apache/hamilton/issues/1649#issuecomment-5771274282)).
- PostHog code remains outside the core library: `ui/frontend` wraps the app in `PostHogProvider` when it is built with `VITE_USE_POSTHOG=true` ([`ui/frontend/src/index.tsx:64`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/ui/frontend/src/index.tsx#L64)) and identifies the user to it ([`App.tsx:111`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/ui/frontend/src/App.tsx#L111)); `ui/sdk` still lists `posthog` as a dependency ([`pyproject.toml:52`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/ui/sdk/pyproject.toml#L52), [`requirements.txt:7`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/ui/sdk/requirements.txt#L7)), though no source file of the software development kit (SDK) imports it; and the `contrib` documentation site loads a PostHog script ([`docusaurus.config.js:97`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/contrib/docs/docusaurus.config.js#L97)). The UI's 0.0.18 release notes list "Removed PostHog telemetry" ([vote](https://lists.apache.org/thread/d4fzmqq4jbsx5m3krdp1qbr0wh9j131s)), but the frontend code above remains behind its build flag. Whether these fall under the same policy was not settled in #1512.
- Run tracking that a user points at their own Hamilton UI (`HamiltonTracker` in the SDK) is user-configured data collection, not project telemetry, and this record does not cover it.

## Alternatives considered

- **Delete `hamilton/telemetry.py` outright.** Rejected in favor of a stub, so that "downstream code that calls `telemetry.disable_telemetry()` continues to work without changes" (#1512).
