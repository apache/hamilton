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

# OpenLineage adapter

This example emits [OpenLineage](https://openlineage.io/) events from an Apache Hamilton dataflow
that reads two SQL tables, aggregates them in Python and writes a report table. It runs locally
against two SQLite files and writes the events to `pipeline.json`; no lineage server, Airflow or
external database is needed.

## The problem it shows

A team reads `orders` and `customers` from a sales database with a query, computes daily revenue,
and writes `daily_revenue` into a warehouse. They want to answer "which tables fed this report?"
and "is that later task reading the same report?" from their lineage backend.

Before this feature, the SQL metadata Hamilton produced carried the query text and, for writes, a bare table name, but
not the database or server. A query read produced a dataset with no table name at all, and the
OpenLineage adapter filed SQL datasets under the *job* namespace, so `daily_revenue` written by one
job and read by another were two unrelated datasets. Getting real lineage meant writing a custom
loader that duplicated connection details.

The built-in `@load_from.sql` / `@save_to.sql` (and `from_.sql` / `to.sql`) materializers record
the datasource they used, and the adapter, created with `sql_dataset_identity="datasource"`, names
the physical tables from it (the default still uses the earlier names; see the adapter reference
below). `pipeline.py` is ordinary Hamilton code:

```python
@load_from.sql(query_or_table=value(REVENUE_QUERY), db_connection=source("sales_db"))
def order_lines(df: pd.DataFrame) -> pd.DataFrame:
    return df

def daily_revenue(order_lines: pd.DataFrame) -> pd.DataFrame:
    return order_lines.groupby(["order_date", "country"], as_index=False)["amount"].sum()

@save_to.sql(table_name=value("daily_revenue"), db_connection=source("warehouse_db"), ...)
def revenue_report(daily_revenue: pd.DataFrame) -> pd.DataFrame:
    return daily_revenue
```

and the events it emits identify the tables by datasource, not by job:

```text
RUNNING input:  sqlite:///.../examples/openlineage/sales.db      customers
RUNNING input:  sqlite:///.../examples/openlineage/sales.db      orders
RUNNING output: sqlite:///.../examples/openlineage/warehouse.db  daily_revenue
```

The query uses a common table expression and aliases; only the two physical tables are reported.
Run against PostgreSQL, the same module reports `postgres://{host}:{port}` namespaces and
`{database}.{schema}.{table}` names. The same table in two databases stays distinct, and a later
read of `daily_revenue` gets the identity it was written under. The module does not change between
a script, a notebook and an orchestrator; only the connections you pass in do.

## Run it

```bash
pip install -r requirements.txt   # apache-hamilton[openlineage] and sqlalchemy
python run.py
```

`run.py` seeds `sales.db`, runs the dataflow with the adapter using a `FileTransport`, prints the
saver's `sql_metadata` and the datasets found in `pipeline.json`. To send events to a running
OpenLineage server such as Marquez instead, swap the client as shown in `run.py`. The notebook
does the same steps interactively.

## Where the metadata comes from

Each SQL loader/saver returns `sql_metadata` with the `source` the connection points at (dialect,
host, port, database, default schema), alongside the query or table name. Custom `@dataloader` /
`@datasaver` functions can produce it too by calling
`hamilton.io.utils.get_sql_metadata(query, df, db_connection=conn)`. The
[materialization guide](https://hamilton.apache.org/concepts/materialization/#sql-metadata-and-lineage)
documents the fields, supported connections and what happens when a datasource cannot be
identified (in-memory SQLite, unknown connection objects): the data still loads, and the adapter
logs why the dataset was left out. The
[adapter reference](https://hamilton.apache.org/reference/lifecycle-hooks/OpenLineageAdapter/)
covers dataset naming, how to migrate from the default identity, and `sql_datasets()`, which other
integrations can call on the same metadata without emitting events.
