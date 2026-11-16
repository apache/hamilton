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

# Architecture Decision Records

Each file here records one design decision: the context that forced it, what was decided, what
it costs, and the alternatives that were rejected. The records outlive the commits and review
threads that produced them, so a later change can tell a deliberate choice from an accident.

- File name: `YYMM-NN-short-title.md`, numbered in order. Numbers are never reused.
- Status: `Accepted`, `Superseded by YYMM-NN`, `Deprecated`, or `Reconstructed from codebase`. An accepted record is not edited to change its decision; write a new record that supersedes it. A record marked `Reconstructed from codebase` was written after the fact, from the code and the history behind it, for a decision the code already embodies: its Status line names where that decision was made, and the status claims no acceptance of the record itself. A reconstructed record is changed the same way as an accepted one.
- Sections: Status, Context, Decision, Consequences, Alternatives considered.

| ADR | Title |
| ----- | ------- |
| [2609-01](2609-01-staged-sql-dataset-identity.md) | Staged, opt-in datasource identity for OpenLineage SQL datasets |
| [2609-02](2609-02-sql-metadata-keeps-1-0-0-filing.md) | SQL metadata keeps the 1.0.0 query/table_name filing; intent travels in `operation` |
| [2609-03](2609-03-resolving-sql-writes-and-statements.md) | How datasource-mode lineage resolves what a SQL write names |
| [2609-04](2609-04-sqlite-attached-databases.md) | SQLite attached databases are named by their own file |
| [2611-01](2611-01-polars-database-sql-metadata.md) | Polars database I/O records `sql_metadata` beside `file_metadata`; the pre-1.0 integration stays legacy-only |
| [2611-02](2611-02-functions-define-nodes.md) | A function defines a node, and its parameter names are its dependencies |
| [2611-03](2611-03-function-modifiers-fixed-lifecycle.md) | Function modifiers annotate a function and resolve in a fixed lifecycle at graph-build time |
| [2611-04](2611-04-version-gated-deprecations.md) | Deprecations name the major release that removes them, through a warn/fail version contract |
| [2611-05](2611-05-extension-registry-autoload.md) | Library integrations load through a dependency-free registry, autoloaded unless the user opts out |
| [2611-06](2611-06-data-adapters-and-materialization.md) | Data I/O is done by registered loader and saver classes that become nodes in the DAG |
| [2611-07](2611-07-lifecycle-adapters.md) | Lifecycle adapters replace graph adapters and result builders as the execution extension point |
| [2611-08](2611-08-apache-hamilton-distribution.md) | Packages are distributed as `apache-hamilton*`; the import name stays `hamilton`, and the `sf-hamilton*` names become redirects |
| [2611-09](2611-09-no-usage-telemetry.md) | Released Hamilton artifacts do not phone home |
