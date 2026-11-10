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
# 2611-08. Packages are distributed as `apache-hamilton*`; the import name stays `hamilton`, and the `sf-hamilton*` names become redirects

**Status:** Reconstructed from codebase (decided 2025-10 on the 1.89.0 release vote, where a binding −1 cited the Incubator's naming rule; carried out from 2026-02 to 2026-05 in [apache/hamilton#1408](https://github.com/apache/hamilton/pull/1408) / commit [7e2ffb84](https://github.com/apache/hamilton/commit/7e2ffb841a812c258cca0c53b01dd14925d3b3fa), [#1488](https://github.com/apache/hamilton/pull/1488), [#1539](https://github.com/apache/hamilton/pull/1539) and [#1588](https://github.com/apache/hamilton/pull/1588))

## Context

Hamilton was published to the Python Package Index (PyPI) as `sf-hamilton` (with `sf-hamilton-sdk`, `-ui`, `-lsp`, and `-contrib`). It entered the Apache Software Foundation (ASF) Incubator in 2025. Its [incubation proposal](https://cwiki.apache.org/confluence/display/INCUBATOR/HamiltonProposal) gives the aims as establishing an open standard, community-driven development, and vendor neutrality: "Many existing graph execution and orchestration tools are tied to commercial platforms." It was relicensed to Apache 2.0 "because we're an apache project now" ([#1335](https://github.com/apache/hamilton/pull/1335), 2025-06). Releases are voted on as source releases.

On the project's own vote for 1.89.0, PJ Fanning wrote that "The source release which is required must have 'incubating' in the name. If you want to also release an sf-hamilton - then you can have 2 tar gz files." ([email](https://lists.apache.org/thread/94y9wso9135hmm3qcwp7rg6hok20rc0d), 2025-09-14). On the general@ vote for 1.89.0-incubating, Justin Mclean voted −1 (binding): "For distribution on PyPI, please see [1]. It appears that you are not following this, particularly in the naming of the artifact" ([email](https://lists.apache.org/thread/8nrk1jtmskk3sn2jnxnpqp6tfvkzr832), 2025-10-06). [1] is the Incubator's [distribution guide](https://incubator.apache.org/guides/distribution.html#pypi): "Artifacts need to be placed in https://pypi.org/project/apache-<project>". Stefan Krawczyk answered that "We need those artifact names to conform" ([email](https://lists.apache.org/thread/gq9y4wvpvbnxgk72gntsspqoq0dpld0l)). The vote passed, and his result email proposed "that we not move the sf_hamitlon* artifacts over to the main Apache Release since everything under there should follow Apache naming conventions", adding "Next time we won't vote on them" ([email](https://lists.apache.org/thread/gkf95nkf5otyj5v95h63yhzplo8tp9v6), 2025-10-10). `apache-hamilton` 1.89.0 [reached PyPI](https://pypi.org/project/apache-hamilton/1.89.0/) as a source distribution on 2025-10-12, the day after `sf-hamilton` 1.89.0.

The repository followed. [7e2ffb84](https://github.com/apache/hamilton/commit/7e2ffb841a812c258cca0c53b01dd14925d3b3fa) gives the reason for renaming the build itself: "This will make it simpler to release things. Since we vote on source releases -- this will make it simpler to do so rather than much post-processing." #1408 adds: "We should only create apache-hamilton artifacts for the source release vote. We can post-process for upload to pypi." Its two approvals date from 2025-10; the rename commit was pushed and merged by its author on 2026-02-21. #1488 renamed and converted the sub-packages "for Apache incubation compliance", with flit "because @potiuk suggested it, and just making this standard across the repo" ([review comment](https://github.com/apache/hamilton/pull/1488#discussion_r2850470985)). Jarek Potiuk had recommended flit on the 1.89.0 vote: it "has 0 dependencies", generates no `.egg-info` artifacts, and spares the project setuptools' "stability" issues ([email](https://lists.apache.org/thread/ccfw895jz9f2gv6pbmfcm9fz7fmcv2xo)). #1488's approval says it was "discussed at length offline with @skrawcz" ([review](https://github.com/apache/hamilton/pull/1488#pullrequestreview-3900538376)).

This record was reconstructed from the release-vote threads on general@incubator.apache.org named below, commit [7e2ffb84](https://github.com/apache/hamilton/commit/7e2ffb841a812c258cca0c53b01dd14925d3b3fa) ("Updates package to be apache-hamilton") and pull request [#1408](https://github.com/apache/hamilton/pull/1408), [#1488](https://github.com/apache/hamilton/pull/1488) (the sub-packages), [#1539](https://github.com/apache/hamilton/pull/1539) and [#1588](https://github.com/apache/hamilton/pull/1588) (the redirects), [`pyproject.toml`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/pyproject.toml#L314-L315), and [`sf-hamilton-redirect/`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/sf-hamilton-redirect).

## Decision

- The distributions are `apache-hamilton`, `apache-hamilton-sdk`, `apache-hamilton-ui`, `apache-hamilton-lsp`, and `apache-hamilton-contrib`, all built with flit.
- The import package is unchanged: `[tool.flit.module] name = "hamilton"` ([`pyproject.toml:314-315`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/pyproject.toml#L314-L315)). User code keeps `import hamilton`.
- Each old name is published as a redirect package ([`sf-hamilton-redirect/`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/sf-hamilton-redirect), `sf-hamilton-{sdk,ui,lsp,contrib}-redirect/`). It has no code of its own and depends on the matching `apache-hamilton*` package at the same version ([`sf-hamilton-redirect/pyproject.toml.template:32`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/sf-hamilton-redirect/pyproject.toml.template#L32)), forwarding its extras "so existing sf-hamilton users get the new release seamlessly" ([cde95ef6](https://github.com/apache/hamilton/commit/cde95ef61bcdebe5c65a6ca875c78b01c77420d4), #1539). The redirects are built with setuptools: "Redirect packages have no Python source code", and flit needs a module to build ([review comment](https://github.com/apache/hamilton/pull/1588#discussion_r3293319716)). Its README tells users to "Replace `sf-hamilton` with `apache-hamilton` in your dependencies" ([`README.md:27`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/sf-hamilton-redirect/README.md#L27)).

## Consequences

- Requirements that name `sf-hamilton` keep installing, and new releases of it pull in `apache-hamilton`, so dependents can migrate gradually. The first redirect release was `sf-hamilton` 1.90.0 (2026-04-25).
- The redirect templates render their extras and Python bound at build time from the packages' own `pyproject.toml` ([#1805](https://github.com/apache/hamilton/pull/1805)). Copied by hand, they had drifted: the main template lacked the `performance` extra, the sub-package templates declared no extras, and all five still accepted Python 3.10 after [#1798](https://github.com/apache/hamilton/pull/1798) raised every `apache-hamilton*` package to `requires-python = ">=3.11, <4"`.
- New sub-packages are named `apache-hamilton-<name>`, and their artifacts are what the release vote covers. Each package is voted on separately: when the four sub-packages came up in one vote, PJ Fanning asked to "stop this vote and start 4 new separate votes" ([email](https://lists.apache.org/thread/mqc6gy3qmngx62x1f7wf2bhnf97f8rz6), 2026-05-26).
- The old names still draw the Incubator's scrutiny: in 2026-05 Justin Mclean noted that "The sf-hamilton package does not carry the ALv2 license field or an Incubator disclaimer" ([email](https://lists.apache.org/thread/59h0yhb993sx3v6cvjt0pgpqkxbbq7wz)).
- Source files carry the ASF license header, enforced by the `insert-license` hooks in [`.pre-commit-config.yaml`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/.pre-commit-config.yaml#L50-L57) (`docs/` and `examples/` are excluded).

## Alternatives considered

- **Keep the `sf-hamilton` distribution names.** Rejected on the 1.89.0 vote: the binding −1 named the artifact names, and the result email moved the `sf_hamilton` artifacts out of the Apache release.
- **Vote on `sf-hamilton` artifacts and rename the source release afterwards.** The release script did this for 1.89.0, copying the tarball to `apache-hamilton-<version>-incubating.tar.gz` ([a2217ff6](https://github.com/apache/hamilton/commit/a2217ff695820d693437d8cde590708a917c7d6a), [#1378](https://github.com/apache/hamilton/pull/1378)). On the vote Stefan Krawczyk allowed that "If we should just post-process the source release then that's fine. But I thought this approach is clearer and more transparent" ([email](https://lists.apache.org/thread/gq9y4wvpvbnxgk72gntsspqoq0dpld0l)), and [7e2ffb84](https://github.com/apache/hamilton/commit/7e2ffb841a812c258cca0c53b01dd14925d3b3fa) chose to build `apache-hamilton` artifacts directly to avoid "much post-processing".
