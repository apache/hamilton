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
# 2611-05. Library integrations load through a dependency-free registry, autoloaded unless the user opts out

**Status:** Reconstructed from codebase (registry decided 2023-01 in commit [c8f8cb56](https://github.com/apache/hamilton/commit/c8f8cb56543e9ff504b62b747caaa22a47ec9d4b), in [stitchfix/hamilton#273](https://github.com/stitchfix/hamilton/pull/273); opt-out autoload decided 2024-08 in [apache/hamilton#1095](https://github.com/apache/hamilton/pull/1095))

## Context

Hamilton supports many dataframe and model libraries (pandas, polars, Spark, Dask, xgboost, mlflow, and others). Features such as `@extract_columns` and the data loaders and savers (2611-06) need to know each library's types. That knowledge lives in `hamilton/plugins/<name>_extensions.py` modules, and only works if the library is installed.

stitchfix/hamilton#273 states the problem it solved: "We had a problem in the decorators (notably extract_columns) that assumed pandas. We need to abstract this out so that other dataframe libraries could be easily used with the decorator." On the polars example that preceded it ([stitchfix/hamilton#263](https://github.com/stitchfix/hamilton/pull/263)), one maintainer proposed that plugins register their own decorator implementations; the other preferred abstracting the "dataframe" instead of the decorator ([review comment](https://github.com/stitchfix/hamilton/pull/263#discussion_r1059830726)), which became the per-library `get_column` and `fill_with_scalar` functions, and wanted the integrations kept apart because they "don't want to add polars as a dependency to main package" ([review comment](https://github.com/stitchfix/hamilton/pull/263#discussion_r1059804731)).

The pull request first put registration in `hamilton.base` ([c9071135](https://github.com/apache/hamilton/commit/c907113560fccbb043c649da66501093e70bf331), 2023-01-12). A reviewer asked "Isn't this a circular dependency?" ([review comment](https://github.com/stitchfix/hamilton/pull/273#discussion_r1070018235)), and hours later [c8f8cb56](https://github.com/apache/hamilton/commit/c8f8cb56543e9ff504b62b747caaa22a47ec9d4b) moved registration into a new `registry` module, which "is not allowed to depend on anything else": extensions import `registry`, and because `registry` imports nothing from Hamilton, loading them creates no circular import.

#1059 (2024-07) reported that importing the driver "takes approximately 4-5 seconds". A maintainer answered that libraries a user has not imported, "Hamilton shouldn't either" ([comment](https://github.com/apache/hamilton/issues/1059#issuecomment-2249671443)). #1095 records the cost of the greedy design: `import hamilton.driver` "tries to import all the extension modules available to the users ... even if these libraries aren't used in the dataflow", which "can introduce slowdowns, memory usage (many Mbs), and warning messages by 3rd party libraries". The how-to it added puts the saving from opting out at "from 2-3 sec to less than 0.5 sec" ([`docs/how-tos/extensions-autoloading.rst`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/docs/how-tos/extensions-autoloading.rst#L19)).

This record was reconstructed from commit [c8f8cb56](https://github.com/apache/hamilton/commit/c8f8cb56543e9ff504b62b747caaa22a47ec9d4b) (2023-01-13, "Refactors and creates a registry module") and the pull request that carried it, [stitchfix/hamilton#273](https://github.com/stitchfix/hamilton/pull/273) ("Introduces *_extensions…", from the project's home before it moved to the Apache Software Foundation, merged 2023-01-16); from [apache/hamilton#1095](https://github.com/apache/hamilton/pull/1095) (merged as [8251ae48](https://github.com/apache/hamilton/commit/8251ae48f90b9a715daa96c419109458494d254e)) and the issue behind it, [#1059](https://github.com/apache/hamilton/issues/1059); and from [`hamilton/registry.py`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py) and [`pyproject.toml`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/pyproject.toml#L48-L56).

## Decision

- [`hamilton/registry.py`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L18-L25) imports only the standard library. It lists the known extensions ([`ExtensionName`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L31-L53)) and holds the per-library type tables, plus [`LOADER_REGISTRY` and `SAVER_REGISTRY`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L220-L221).
- [`registry.initialize()`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L100-L114) tries to import every listed extension and skips any that raises `ImportError` (its library is missing), `NotImplementedError`, or a `Warning` (a warning raised as an error, caught since [157ecd60](https://github.com/apache/hamilton/commit/157ecd60c8371be6c479bc2dbed470487c948c74)). `hamilton.function_modifiers.base` calls it at import time ([`hamilton/function_modifiers/base.py:41`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/function_modifiers/base.py#L41)); commit [2489423d](https://github.com/apache/hamilton/commit/2489423dd6ccb74a38d2266536424356c7d692b3), in stitchfix/hamilton#273, put the call there because "Ray serialization is the cause of this move" and "decorators are the only thing that need the registry right now".
- Autoload stays the default. Users can opt out with [`registry.disable_autoload()`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L117-L122), the `HAMILTON_AUTOLOAD_EXTENSIONS=0` environment variable, or a persistent [`~/.hamilton.conf`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L56) entry set by the `hamilton-disable-autoload-extensions` command ([`pyproject.toml`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/pyproject.toml#L209-L210)). A user who opts out loads what they need with [`registry.load_extension(name)`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/hamilton/registry.py#L79-L97) or by importing the extension module.
- Third-party libraries an integration needs are optional extras in `pyproject.toml` (`[project.optional-dependencies]`), not core dependencies.

## Consequences

- A new integration adds an `ExtensionName` entry and a `<name>_extensions.py` module. That module must provide `register_types`, `get_column_<name>`, and `fill_with_scalar_<name>`, unless it sets `COLUMN_FRIENDLY_DF_TYPE = False` (`registry.load_extension`). `register_types` answers a review question on stitchfix/hamilton#273, "Might be nice to have modules add their own types?" ([review comment](https://github.com/stitchfix/hamilton/pull/273#discussion_r1070016188)).
- Importing Hamilton in an environment that has many libraries installed still pays for the import of every matching extension, unless the user opts out. Greedy loading has broken imports outright: users with pydantic older than 2.0 installed hit errors "even if not using Pydantic" until pydantic moved into its own extension ([apache/hamilton#1152](https://github.com/apache/hamilton/pull/1152)).
- Disabling autoload must happen before `hamilton.driver` is imported (`disable_autoload` docstring).
- Opting out does not remove the import cost of pandas and numpy, which are still core dependencies ([`pyproject.toml`](https://github.com/apache/hamilton/blob/ef88b1e96140a01f3d72967316c2335f8b62a067/pyproject.toml#L48-L54), `dependencies`); [apache/hamilton#1246](https://github.com/apache/hamilton/issues/1246), on profiling the driver's imports, is open. A maintainer wrote on [apache/hamilton#918](https://github.com/apache/hamilton/issues/918#issuecomment-2150392609) (2024-06-05) that pandas is "only left there for legacy reasons" and that "the library should have zero dependencies". That issue is open, and removing pandas and numpy is not decided.

## Alternatives considered

- **Make loading opt-in by default.** Rejected in #1095: "Since many features (`@extract_columns`, materializers, and more) rely on this extension registry, changing the default behavior would introduce many hard-to-track breaking changes."
- **Load only the extensions whose library the user has already imported.** #1095's first version did this. A reviewer asked why that clause was needed ([review comment](https://github.com/apache/hamilton/pull/1095#discussion_r1717623413)), and the author proposed three modes, greedy, lazy and disabled, noting "Lazy might be more valuable for development and Disabled better in prod" ([review comment](https://github.com/apache/hamilton/pull/1095#discussion_r1718547747)). The lazy clause was removed before merge ([5bf96dc1](https://github.com/apache/hamilton/commit/5bf96dc1d90909b2f058f437afb92a416c8a9a04)); why is not recorded.
- **Keep registration in `hamilton.base`.** The first draft of stitchfix/hamilton#273 did; [c8f8cb56](https://github.com/apache/hamilton/commit/c8f8cb56543e9ff504b62b747caaa22a47ec9d4b) moved it out to avoid circular imports between core and the extension modules.
- **An object as the extension interface.** The body of stitchfix/hamilton#273 weighed an object one has to implement, and judged "this abstraction right now is simpler -- the housing unit is the module", with "trying to import the modules and having them determine how to error" as the loading rule.
