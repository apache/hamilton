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

# 2609-04. SQLite attached databases are named by their own file

**Status:** Accepted (2026-09, apache/hamilton#1720)

## Context

In SQLite a schema names a database *file*: `main`, `temp`, or anything attached with `ATTACH`.
Datasource naming used the main file's namespace for every table. So `reporting.orders`, stored
in an attached `other.db`, was attributed to `main.db`: the wrong physical datasource.

## Decision

- For a standard-library `sqlite3` connection, metadata inspection reads `PRAGMA database_list`
  on that same connection and records `source["attached"]` as a schema-name→absolute-path map. It
  opens no connection and starts no transaction. For URL strings and SQLAlchemy objects the
  mapping cannot be known without opening a connection, so `attached` is `None`.
- A table qualified by an attached schema gets the attached file's namespace, and the name
  `{table}`. `main` or no schema uses the main file. Names are compared case-insensitively, as
  SQLite does.
- Left out with a note, never attributed to the main file: an unknown mapping (`attached` is
  `None`), an unattached schema, `temp`, and unqualified tables of an in-memory main database. An
  in-memory main connection with files attached keeps its mapping.

## Consequences

- A write to `orders` and a read of `main.orders` resolve to the same dataset.
- Attached-database lineage needs a raw `sqlite3` connection. Other connection forms leave those
  tables out and explain why.

## Alternatives considered

- **Keep `{schema}.{table}` under the main file's namespace** (first version). Rejected:
  misattributes the physical datasource.
- **Run the PRAGMA through a SQLAlchemy connection.** Rejected: SQLAlchemy 2's autobegin would
  start a transaction, which breaks the read-only inspection guarantee.
