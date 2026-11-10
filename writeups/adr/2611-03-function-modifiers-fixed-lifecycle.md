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
# 2611-03. Function modifiers annotate a function and resolve in a fixed lifecycle at graph-build time

**Status:** Reconstructed from codebase (decided 2021-12 in commit [bc7c089d](https://github.com/apache/hamilton/commit/bc7c089d3715ebd5936dd0beed8428ecf7e69ea8), "Implements opinionated decorator lifecycle", merged 2022-02 in [stitchfix/hamilton#28](https://github.com/stitchfix/hamilton/pull/28) for release 1.3.0; phases added since are dated below)

## Context

**Rationale partly recovered.** Why stitchfix/hamilton#28 put the phases in this order, and which other orders were weighed then, are not recorded; the pull requests that added phases later say why they did.

By 2611-02, one function is one node. Decorators were needed where one function should become zero nodes (`@config.when`), several nodes (`@parameterize`, `@extract_columns`), or nodes with extra metadata or checks (`@tag`, `@check_output`). The commit "adds to the set of decorators that can be applied to a node, and puts them in a uniform setting".

Both people on stitchfix/hamilton#28 described it as mostly a refactor. The reviewer, Stefan Krawczyk, asked "Otherwise the decorator lifecycle is largely a refactor of existing behavior, right?" ([review](https://github.com/stitchfix/hamilton/pull/28#pullrequestreview-829399377)), and the author, Elijah ben Izzy, answered that it was "a refactor of existing behavior. Technically this allows models + parametrization together (whereas before it wouldn't)" ([comment](https://github.com/stitchfix/hamilton/pull/28#issuecomment-991376043)). The pieces it unified date from 2019:
- Expanders, and attaching to a function instead of wrapping it: [889bc1c8](https://github.com/apache/hamilton/commit/889bc1c8a6a7ab44540949cf830d9efb315c7113) "Modified the graph module to ask for the nodes a function produces (when annotated), rather than assuming each function maps to one node."
- Resolvers running first: [36b18e54](https://github.com/apache/hamilton/commit/36b18e54f1163a653843df4d9d6c34e5e30c3394) "we create a new abstraction, FunctionResolver, that allows us to resolve a function before modifying it", while noting that a proper design would need "a better set of abstractions".

Sensitivity to stacking order was one concrete motive. A commit in stitchfix/hamilton#28 ([2fb3c60a](https://github.com/apache/hamilton/commit/2fb3c60a951c337974c552beb5044f345eb34bff)) records that `@config.when` renamed the function, but "this broke depending on decorator ordering".

This record was reconstructed from commit [bc7c089d](https://github.com/apache/hamilton/commit/bc7c089d3715ebd5936dd0beed8428ecf7e69ea8) (2021-12-08) and the pull request that carried it, [stitchfix/hamilton#28](https://github.com/stitchfix/hamilton/pull/28) (from the project's home before it moved to the Apache Software Foundation, merged 2022-02-06); from the 2019 commits that introduced resolvers and expanders; from the [`resolve_nodes` docstring](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L830), [`writeups/decorators.md:640-665`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/writeups/decorators.md#L640-L665) ("A mental model for decorators"), and [`docs/concepts/function-modifiers.rst:25`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/concepts/function-modifiers.rst#L25). The sources name two goals: one "uniform setting" for all decorators, and decorators that "should be insensitive to ordering".

## Decision

- A function modifier does not wrap the function. `NodeTransformLifecycle.__call__` validates the function and appends the modifier object to a list attribute on it, named for the modifier's lifecycle phase ([`hamilton/function_modifiers/base.py:112-132`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L112-L132)). The function stays callable as written.
- When the graph is built, [`resolve_nodes`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L830) (called from [`hamilton/graph.py:190`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/graph.py#L190)) applies the attached function modifiers by phase, in a fixed order between phases:
  1. resolvers (`NodeResolver`, such as `@config.when`) decide whether the function exists in this graph, and any resolver returning `None` drops it; dynamic resolvers (`@resolve`, added 2023-03 in [apache/hamilton#108](https://github.com/apache/hamilton/pull/108)) first turn config into further function modifiers, which join their phases after the statically attached ones ([`get_node_decorators`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L754-L766));
  2. exactly one creator (`NodeCreator`, by default the plain function) produces the initial nodes;
  3. injectors (`NodeInjector`, added 2023-07 in [#221](https://github.com/apache/hamilton/pull/221)) feed values into the subdag; injection had been a creator, which "could only be run once", and as a subdag modifier it can run several times ([6c6528e3](https://github.com/apache/hamilton/commit/6c6528e3218d2c87c52bafa69de512573123ba64));
  4. expanders (`NodeExpander`): any pre-expanders (added 2026-09 in [#1650](https://github.com/apache/hamilton/pull/1650), so that "`@inject` can run before regular expanders such as `@parameterize`"), then at most one regular expander, turn one node into many;
  5. transformers (`NodeTransformer`), then decorators (`NodeDecorator`, added 2022-02 for tags in [stitchfix/hamilton#83](https://github.com/stitchfix/hamilton/pull/83)), modify the resulting nodes.

  Within one phase, function modifiers apply in the order they were stacked, from the bottom up ([`base.py:129`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L129)).
- A layering function modifier chooses which of the generated nodes it modifies with `target_`, added in [stitchfix/hamilton#316](https://github.com/stitchfix/hamilton/pull/316) ([b848a72d](https://github.com/stitchfix/hamilton/commit/b848a72d37c3b365c5d5403debcb5551c2a3f82a)). `None` means the "final" nodes, that is, nodes no other node from the same function depends on. `...` means all nodes, and a string or list names nodes explicitly ([`writeups/decorators.md:657-665`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/writeups/decorators.md#L657-L665), [`NON_FINAL_TAG`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L386)). In review, Stefan Krawczyk found that "going between function and nodes is confusing", and Elijah ben Izzy answered "let's revisit that and see how users react" ([review comment](https://github.com/stitchfix/hamilton/pull/316#discussion_r1110472921)). The default follows a 2022 proposal that "tags associate to only the last node in a subdag created by a node decorator" ([stitchfix/hamilton#4](https://github.com/stitchfix/hamilton/issues/4#issuecomment-1048476479)).
- Each function modifier sees only the config keys it declares ([`filter_config`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L725)). The commit that added it, in the same pull request ([9bdcaf1f](https://github.com/apache/hamilton/commit/9bdcaf1fbfa9183c3729d2cf368d582fc09f671e), 2023-02) gives the reason: "This allows for inspection/visibility, and will be essential in checkpointing/storage options. We want decorators to declare these upfront, rather than relying on the internals of the decorators to break, enabling clearer error messages".

## Consequences

- One function maps to zero, one, or many nodes ([`writeups/decorators.md:648-650`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/writeups/decorators.md#L648-L650)). "Function" and "node" are different terms, and code that walks the graph must not assume they correspond one to one.
- Hamilton decorators "should be insensitive to ordering" ([`docs/concepts/function-modifiers.rst:25`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/concepts/function-modifiers.rst#L25)), and the same page warns that non-Hamilton decorators, such as `@retries` or `@time`, are not. Insensitivity is an aim rather than a guarantee: on one combination that failed, Elijah ben Izzy wrote there was "no inherent reason why this should work -- its an implementation detail that it doesn't" ([comment](https://github.com/apache/hamilton/issues/160#issuecomment-1535150079)), and #1650 made that combination work in 2026; [#748](https://github.com/apache/hamilton/issues/748) (`@inject` with `@pipe`) is open; and [#57](https://github.com/apache/hamilton/issues/57), "Clarify behavior of decorator ordering", is open, asking the project to "make clear our philosophy and resolution method".
- Config acts during construction of the directed acyclic graph (DAG), through resolvers, so it is fixed when the Driver is built. [`writeups/basics.md:137-138`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/writeups/basics.md#L137-L138) states the reason: config "is used not just to feed data to the DAG, but also to determine the structure of the DAG. As such, it is passed in to the constructor". Changing config means building a new Driver ([`docs/concepts/builder.rst:96`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/concepts/builder.rst#L96)). Config must not be used to replace computed values; `overrides` on `execute()` does that ([`writeups/basics.md:140-142`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/writeups/basics.md#L140-L142)).
- A new function modifier must fit one of the phases. Two regular expanders on one function are rejected (the `len(regular_expanders) > 1` check in [`resolve_nodes`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L879)).

## Alternatives considered

- **Other phase orders, or applying function modifiers in stacking order.** For the order stitchfix/hamilton#28 set, not recorded: no issue, pull request or document found weighs them.
- **An `augment` decorator.** Added in stitchfix/hamilton#28 and removed before merge ([e7866102](https://github.com/apache/hamilton/commit/e78661022a7deef84e6c02c8029986907674141a)). The reviewer objected that "it is not clear at all what the outputs are here" ([review comment](https://github.com/stitchfix/hamilton/pull/28#discussion_r800111209)); the author agreed it was "not necessary. It loses type information." ([review comment](https://github.com/stitchfix/hamilton/pull/28#discussion_r800115984)).
- **A linter that reorders decorators.** Floated on #57 ("can we create a linter that reorders decorators?") and not built.
