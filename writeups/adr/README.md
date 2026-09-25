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
- Status: `Accepted`, `Superseded by YYMM-NN`, or `Deprecated`. An accepted record is not edited to
  change its decision; write a new record that supersedes it.
- Sections: Status, Context, Decision, Consequences, Alternatives considered.

| ADR | Title |
| ----- | ------- |
| [2609-01](2609-01-staged-sql-dataset-identity.md) | Staged, opt-in datasource identity for OpenLineage SQL datasets |
| [2609-02](2609-02-sql-metadata-keeps-1-0-0-filing.md) | SQL metadata keeps the 1.0.0 query/table_name filing; intent travels in `operation` |
| [2609-03](2609-03-resolving-sql-writes-and-statements.md) | How datasource-mode lineage resolves what a SQL write names |
| [2609-04](2609-04-sqlite-attached-databases.md) | SQLite attached databases are named by their own file |
