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

# 2609-03. How datasource-mode lineage resolves what a SQL write names

**Status:** Accepted (2026-09, apache/hamilton#1720)

## Context

Under ADR 0002, a write's string may sit under `query` or `table_name`. It may be a table name
(`daily revenue`, `SELECT results`, `USER_SELECTIONS`) or, for custom savers, a statement
(`INSERT INTO t SELECT ...`). `sql_datasets()` must name the tables written, and it must never
invent a dataset named after SQL text or report a table name as the job's SQL.

Several intermediate rules failed review:

- A keyword list for spotting statements without a parser leaked. `DROP`, `TRUNCATE`, `BEGIN` and
  `(` all slipped through.
- Treating every write string as a name turned statements into datasets.
- Building the job's `sql` facet from the raw metadata `query` reported `USER_SELECTIONS` as the
  job's SQL.

## Decision

For a write (`operation="write"`), take the string from either key:

1. A plain identifier (optionally qualified) is the table. No parser is needed.
2. Anything else is parsed with `openlineage-sql`:
   - a statement that writes tables contributes those tables, plus the tables it reads;
   - a statement that only reads tables is left out, with a note;
   - a string that names no table at all is the table name.
3. Without a parse (parser missing or raising), a non-plain string is left out with a note. A name
   and a statement cannot be told apart then.

For a read, a `table_name` that is not a plain identifier is parsed as SQL rather than used as a
name.

The job's `sql` facet comes from `SqlDatasets.query`, the statement actually resolved. It is set
only for a string the metadata recorded as a read query, or one whose parse names tables.

## Consequences

- No dataset is ever named after SQL text, and table names are not reported as the job's SQL.
- On Windows (no `openlineage-sql`), a written name that is not a plain identifier is left out of
  lineage with a note. This is documented, and it only affects datasource mode.
- Known limitation: a table *read* by a name the metadata files as a query (`SELECT_LOG`,
  `select-log`) cannot be told apart from a statement. The name is reported as the job's SQL and
  no input dataset is emitted. For upper-case `SELECT` names, the previous adapter did the same.

## Alternatives considered

- **Keyword list to spot statements without a parser.** Rejected: it leaks by construction.
- **Repeat pandas' `has_table` check to settle table-versus-query reads.** Rejected: a second
  database round-trip per read for a rare naming case; lineage stays side-effect free instead.
- **Always trust a write's string as the table name.** Rejected: it names datasets after
  statements.
