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
# 2611-07. Lifecycle adapters replace graph adapters and result builders as the execution extension point

**Status:** Reconstructed from codebase (decided 2023-12 in [apache/hamilton#592](https://github.com/apache/hamilton/pull/592) / commit [b7e74b76](https://github.com/apache/hamilton/commit/b7e74b76938564b6a40e9a91b865a571617f011f), tracked in umbrella issue [apache/hamilton#605](https://github.com/apache/hamilton/issues/605))

## Context

Before this change, execution was customized through `HamiltonGraphAdapter` and result builders. `HamiltonGraphAdapter` arrived in 2022-02 (commit [2b610869](https://github.com/apache/hamilton/commit/2b6108694f186b5421b65b6e4bf032b231bc64c5), in [stitchfix/hamilton#47](https://github.com/stitchfix/hamilton/pull/47)), whose author "decided to have it extend ResultMixin to simplify things", tying execution and result building into one class. The commit says the lifecycle work was "meant to: 1. Replace GraphAdapters 2. Replace ResultBuilders 3. Add new capabilities to pre/post node execution 4. Consolidate some of the extra things we'd considered adding/additional features we have (data quality potentially, logging to OpenTel, debugging, etc...)".

The post that announced it, "[Customizing Hamilton's execution with lifecycle hooks](https://blog.dagworks.io/p/customizing-hamiltons-execution-with)" (2024-01), linked from [#605's closing comment](https://github.com/apache/hamilton/issues/605#issuecomment-1898837617), gives the aim: "Rather than stretching ourselves thin by reinventing the execution, auditing, telemetry, and validation wheels for every conceivable context, we have decided to keep Hamilton itself simple and add the ability to build/integrate any of these capabilities yourself!"

This record was reconstructed from commit [b7e74b76](https://github.com/apache/hamilton/commit/b7e74b76938564b6a40e9a91b865a571617f011f) (2023-12-22, "Implements Lifecycle Customizations") and the pull request that carried it, [#592](https://github.com/apache/hamilton/pull/592) (opened 2023-12-17, merged 2023-12-26); from umbrella issue [#605](https://github.com/apache/hamilton/issues/605), opened afterward with the commit's message; from the module docstring of [`hamilton/lifecycle/base.py:18-43`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L18-L43); and from the post the issue's closing comment links. The commit message has a section "What decisions have been made that might impact design?", so most of the reasoning is recovered. #592 was written by Elijah ben Izzy; Stefan Krawczyk approved it, writing "I have run the branch locally and it seems to not introduce any regressions" ([review](https://github.com/apache/hamilton/pull/592#pullrequestreview-1796091436)).

## Decision

- Execution is customized by lifecycle adapters of three kinds. *Hooks* augment execution. Several hooks of the same kind can be layered and all run, for example `NodeExecutionHook` and `GraphExecutionHook`. *Methods* replace a step of Hamilton's execution, for example `NodeExecutionMethod` and `ResultBuilder`, and "can not (currently) be layered" ([`hamilton/lifecycle/base.py:24-25`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L24-L25)). *Validators* check the graph or nodes and were added in [#633](https://github.com/apache/hamilton/pull/633).
- Each stage is a single-method class with a unique name, registered through the [`lifecycle` decorator](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L184). Stages do not share a common base class or metaclass. The commit gives the reason: "This allows us to be flexible with the function structure, and, more importantly, allows for easier multiple inheritance to ensure MRO is simple to find." MRO is Python's method resolution order. One user class can implement several stages by inheriting several application programming interface (API) classes.
- There are two layers. Internal base classes in `hamilton/lifecycle/base.py` are "*not* a public facing API", and the post says they "may not necessarily be stable between minor/patch versions". Users extend the classes in `hamilton/lifecycle/api.py`, whose methods take keyword arguments plus `**future_kwargs` "to ensure we can add (but not subtract) parameters and nothing will break".
- Each stage can have a sync and an async version.
- The package was first called `customization`; it became `lifecycle` at the reviewer's suggestion, the author agreeing it was "more consistent and descriptive enough" ([review comment](https://github.com/apache/hamilton/pull/592#discussion_r1435888832)).
- The Driver groups the adapters it receives into a [`LifecycleAdapterSet`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L880) ([`hamilton/driver.py:336`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/driver.py#L336)) and calls stages through it.
- Legacy APIs remain as adapters built on the new ones. [`lifecycle.api.GraphAdapter`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/api.py#L121-L127) composes the node-execution, result, input-validation, and edge-type-check methods, and [`hamilton.base.HamiltonGraphAdapter`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/base.py#L408) extends it. [`LegacyResultMixin`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/api.py#L106) keeps the old static `build_result`, and [`hamilton.base.ResultMixin`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/base.py#L42) extends it.

## Consequences

- Later execution features ship as lifecycle adapters: tracing and tracking (`DDOGTracer`, `MLFlowTracker`), `OpenLineageAdapter`, `ProgressBar`, `SlackNotifierHook`, `PDBDebugger`, and others ([`docs/reference/lifecycle-hooks/`](https://github.com/apache/hamilton/tree/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/reference/lifecycle-hooks)). Caching is one too: the first cache adapter ([#766](https://github.com/apache/hamilton/pull/766)) is now deprecated, and its replacement, [`HamiltonCacheAdapter`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/caching/adapter.py#L194-L196) ([#1104](https://github.com/apache/hamilton/pull/1104)), is built on the lifecycle base classes.
- An adapter set can hold any number of hooks but at most one implementation of each method ([`base.py:963`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L963)). The cost is concrete: caching uses the single `do_node_execute()` method, so it "is currently incompatible with other adapters leveraging it", such as `PDBDebugger` ([`docs/reference/caching/caching-logic.rst:63`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/reference/caching/caching-logic.rst#L63)).
- Existing `GraphAdapter` and `ResultMixin` subclasses keep working, but the two systems coexist. Code in `hamilton.base` still carries the legacy class hierarchy. [b7e74b76](https://github.com/apache/hamilton/commit/b7e74b76938564b6a40e9a91b865a571617f011f) listed a "3. Deprecation" step for graph adapters that has not happened; the documentation now presents them as "special cases" of lifecycle hooks that "implement multiple lifecycle customizations in a single place" ([`docs/reference/graph-adapters/index.rst:6`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/reference/graph-adapters/index.rst#L6)).
- #592's author also meant to retire `Driver.raw_execute`: "we don't want people to use raw_execute anymore, just the driver builder" ([review comment](https://github.com/apache/hamilton/pull/592#discussion_r1435775253)). It is still in [`hamilton/driver.py`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/driver.py#L613).
- Adding a stage means four steps listed in the `base.py` docstring: a single-method class, the `lifecycle` decorator, an entry in the `LifecycleAdapter` type, and a call at the right point in execution. They are not always all taken: `BaseDoRemoteExecute` ([#1103](https://github.com/apache/hamilton/pull/1103)) is missing from the [`LifecycleAdapter` type](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/lifecycle/base.py#L850-L877).

## Alternatives considered

- **One base class or metaclass for all lifecycle stages.** Rejected in favor of registration, for flexible function signatures and simple multiple inheritance ([b7e74b76](https://github.com/apache/hamilton/commit/b7e74b76938564b6a40e9a91b865a571617f011f)).
- **Keep extending `GraphAdapter` and result builders.** The change was explicitly meant to replace them. The commit notes that async "never worked with graph adapters". It does not otherwise say why extending them was rejected.
- **One abstract class per hook with `before` and `after` methods.** Prototyped in 2023-07 as `hamilton/execution/hooks.py_backup` (commit [d410e126](https://github.com/apache/hamilton/commit/d410e12605f078903198d88204925a7073b3633f), in [#220](https://github.com/apache/hamilton/pull/220)) and deleted from that pull request as "not needed now" ([review comment](https://github.com/apache/hamilton/pull/220#discussion_r1272709517)).
- **Hooks that wrap functions when the graph is built.** Raised in review on #592 and deferred: the author answered that decorators already act as such hooks, and that he wanted "to push that off till later" ([review comment](https://github.com/apache/hamilton/pull/592#discussion_r1435889364)).
