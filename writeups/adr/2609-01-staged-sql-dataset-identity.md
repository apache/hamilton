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

# 2609-01. Staged, opt-in datasource identity for OpenLineage SQL datasets

**Status:** Accepted (2026-09, apache/hamilton#1720)

## Context

`OpenLineageAdapter` has always named SQL loader/saver datasets under the adapter's *job*
namespace with the bare `table_name`. Metadata version 1.1.0 records the datasource a SQL node
used, which allows naming datasets the OpenLineage way (`postgres://host:port` +
`db.schema.table`, `sqlite://{file}` + `table`). That lets a report written by one job connect
to the job that reads it.

Switching names changes the identity of every existing SQL dataset. Lineage history stops
connecting, and anything keyed to the old names in a lineage backend (ownership, tags, alerts,
policies) silently stops matching. Datasource naming also needs `openlineage-sql`, which has no
Windows wheel, and it leaves out datasets it cannot identify instead of guessing. So an upgrade
alone would make some datasets disappear.

## Decision

- `OpenLineageAdapter(..., sql_dataset_identity="legacy" | "datasource")`. The default stays
  `"legacy"`, which emits exactly what earlier releases emitted (namespace, name and facets). It
  is pinned in tests against the previous adapter's output. The legacy path never imports
  `openlineage-sql`.
- Leaving the option unset emits one `FutureWarning` per adapter, the first time a SQL node runs.
  It names both values, says the default will change in a future **major** release, and links the
  migration steps. Passing either value explicitly silences it.
- The warning and every lineage conversion run inside the adapter's never-fail boundary. A
  warnings filter set to `error` is caught and logged, so lineage can never fail a node whose SQL
  operation already succeeded. There is no strict mode.
- `create_input_dataset` / `create_output_dataset` keep their SQL handling and return shapes,
  because they are public module functions.
- An invalid value raises `ValueError` at construction, never during a run.

## Consequences

- Upgrading changes no dataset identity. Users migrate on purpose: install `openlineage-sql`,
  dry-run with `FileTransport`, move backend metadata, then opt in. This is documented in
  `docs/reference/lifecycle-hooks/OpenLineageAdapter.rst`.
- Two naming paths exist until the default flips. The flip is a breaking change reserved for a
  major release.

## Alternatives considered

- **Switch the default immediately** (the PR's first version). Rejected: it silently breaks every
  existing lineage consumer, which is the maintainer's review objection.
- **Warn on every node, or raise on the legacy default.** Rejected: noisy, and raising turns
  lineage into a way to fail successful data work.
- **Keep only legacy and publish datasource naming via `sql_datasets()` alone.** Rejected: the
  adapter is where users get lineage, and a staged path gives them a migration route.
