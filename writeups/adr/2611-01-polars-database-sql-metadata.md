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

# 2611-01. Polars database I/O records `sql_metadata` beside `file_metadata`; the pre-1.0 integration stays legacy-only

**Status:** Accepted (2026-11, apache/hamilton#1743)

## Context

`PolarsDatabaseReader` and `PolarsDatabaseWriter` described database I/O with `file_metadata` only, filing the query or table name as a file path. With `OpenLineageAdapter(sql_dataset_identity="datasource")` (ADR 2609-01), the adapter therefore could not identify the database and emitted FileSystem datasets named after the SQL text.

ADR 2609-01 also promises that the default legacy mode emits exactly what earlier releases emitted. The legacy builders read `file_metadata` before `sql_metadata`, so legacy dataset names for these nodes come from `file_metadata`.

Hamilton keeps a separate integration for polars <1.0, deprecated and loaded only for those versions.

## Decision

- The Polars database classes return `sql_metadata` in addition to `file_metadata`, not instead of it. Legacy mode keeps reading `file_metadata` and emits the same datasets as before, while datasource mode reads `sql_metadata`. `file_metadata` is removed from these classes only in the major release that makes `"datasource"` the default.
- The pre-1.0 integration supports legacy lineage only. Its classes record `sql_metadata` without a datasource, and their `notes` ask the user to upgrade polars, so datasource mode emits no dataset for them and logs the note. This is a support boundary of the deprecated integration, not a limit of polars <1.0, whose connections `get_sql_source` could identify.

## Consequences

- Default-mode users see the `FutureWarning` that ADR 2609-01 introduces for SQL nodes, now for Polars database nodes too. `sql_dataset_identity="legacy"` silences it.
- Until the default flips, these classes carry two descriptions of the same I/O, and the legacy description keeps its query-as-path values.
- Pre-1.0 users who opt into datasource mode get no dataset for database nodes until they upgrade polars.

## Alternatives considered

- **Replace `file_metadata` with `sql_metadata` now.** Rejected: it renames legacy datasets (the read would lose its node-based name), breaking ADR 2609-01's promise for default-mode users.
- **Leave the pre-1.0 classes with `file_metadata` only.** Rejected: datasource mode would then emit the FileSystem datasets this change removes, silently, instead of saying how to get datasource lineage.
- **Give the pre-1.0 classes datasource lineage.** Rejected: it extends an integration scheduled for removal.
