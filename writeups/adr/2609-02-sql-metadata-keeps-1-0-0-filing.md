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

# 2609-02. SQL metadata keeps the 1.0.0 query/table_name filing; intent travels in `operation`

**Status:** Accepted (2026-09, apache/hamilton#1720)

## Context

`get_sql_metadata(query_or_table, results)` files its string under `query` if it contains
`SELECT`, and under `table_name` otherwise. The legacy OpenLineage names are built from those
keys, so changing the filing changes dataset names. One such change is a lower-case `select`
read moving from `table_name` to `query`: on the previous adapter it produced a dataset named
after the query text.

The filing is also wrong for some inputs. A written table named `USER_SELECTIONS` is filed as a
query. The first version of this change replaced the rule with "contains whitespace", which
misfiled `PandasSqlWriter(table_name="daily revenue")` as a read query and dropped its output
dataset.

## Decision

- Keep the 1.0.0 rule for the two-argument form and for every write. The only new filing is on
  reads: a string whose first word after SQL comments is `select` or `with` (any case) is a query.
  Detection is a linear scan, because a regex over repeated comments backtracked exponentially.
- Add keyword-only `operation="read" | "write"`. `PandasSqlReader`/`PandasSqlWriter` pass it, so
  consumers know that a write's string is the target, whichever key holds it.
- The legacy lineage builders re-derive the 1.0.0 filing. They move only the one case 1.1.0
  changed (a query-only lower-case read) back to `table_name`, and only for metadata whose
  `__version__` is newer than 1.0.0. Hand-built metadata, such as the `{query, table_name}` dicts
  older examples built, is used exactly as given.
- New keys (`schema`, `operation`, `source`, `notes`) are additive, and `__version__` is `1.1.0`.

## Consequences

- Existing consumers of `sql_metadata` see the same `query`/`table_name` values for writes and
  for two-argument calls. Default-mode lineage names are unchanged for every string tested.
- `query` does not always hold SQL. A written name containing `SELECT` sits there, so lineage code
  must use `operation` and not the key alone (see ADR 0003).

## Alternatives considered

- **Whitespace heuristic** (first version). Rejected: it misclassifies valid table names.
- **Always file a write's string as `table_name`.** Rejected: it changes existing metadata values
  for names containing `SELECT`, contrary to the compatibility goal.
- **Refile every query-only lower-case string in the legacy builders.** Rejected: it renamed
  datasets for hand-built metadata, hence the version gate.
