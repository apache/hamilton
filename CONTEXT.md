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

# Apache Hamilton

A Python library that builds a directed acyclic graph (DAG) of data transformations from plain Python functions, whose names are the nodes and whose parameters are the dependencies.

This glossary records what words mean in this project where ordinary usage or generic tool knowledge would mislead. Add a term when the project settles one.

## Language

- **adapter** — three different things share this word. A *data adapter* is a `DataLoader`/`DataSaver` class registered by name in the adapter registry (`hamilton/registry.py`). A *legacy graph adapter* is a `HamiltonGraphAdapter` subclass (`hamilton/base.py`). A *lifecycle adapter* is a hook, method, or validator passed to `Builder.with_adapters` (`hamilton/lifecycle/`). Name which one you mean.
- **function vs node** — a *function* is what the user writes in a module; a *node* is one step in the DAG. One function yields zero, one, or many nodes (function modifiers expand, rename, or drop them), so never assume one-to-one.
- **function modifier** — Hamilton's name for its decorators (`@extract_columns`, `@parameterize`, `@config.when`, …). A function modifier changes how a function compiles into nodes when the graph is built; unlike a plain Python decorator it does not wrap the call. Modifiers resolve in a fixed order of phases, one per kind of modifier: resolvers, creators, injectors, expanders, transformers, and decorators (see [`writeups/adr/2611-03-function-modifiers-fixed-lifecycle.md`](writeups/adr/2611-03-function-modifiers-fixed-lifecycle.md)). `NodeDecorator` is the base class of the last of those phases, so "decorator" in the code can mean that phase rather than every modifier.
- **config / inputs / overrides** — *config* shapes the DAG and is fixed when the driver is built; *inputs* are per-run values for nodes nothing in the DAG produces; *overrides* replace values the DAG would otherwise compute, skipping their upstream work. Putting a value in the wrong one changes the graph or silently skips computation.
- **result builder** — combines the requested outputs into the return value of `execute()`. The default differs by entry point. The legacy `Driver(config, module)` uses `PandasDataFrameResult`. `driver.Builder` adds none, so `execute()` returns the outputs as a dict, as `DictResult` would. The same DAG can therefore return different types.
- **hook / method / validator** — the three kinds of lifecycle adapter. *Hooks* observe or augment execution and stack freely; *methods* replace one step of execution, and only one adapter may implement each method (a sync and an async implementation count separately); *validators* check the graph or its nodes when it is built.
- **materializer vs data loader/saver decorators** — *materializers* (`Driver.materialize` with `from_`/`to`) and `@load_from`/`@save_to` pick a registered data adapter by name and type. `@dataloader`/`@datasaver` instead wrap a user function that returns data plus metadata, with no registry involved. They are separate extension points.
- **extension vs plugin module** — `hamilton/plugins/<lib>_extensions.py` modules are *extensions*: the registry autoloads them to register types and data adapters. `hamilton/plugins/h_<lib>.py` modules are *plugins* the user imports explicitly for adapters and helpers. Both live in `hamilton/plugins/`, so a new integration has to choose which kind it is.
