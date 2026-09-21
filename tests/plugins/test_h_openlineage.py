# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import json
import logging
import sqlite3

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from hamilton import ad_hoc_utils, driver
from hamilton.function_modifiers import load_from, save_to, source, value
from hamilton.io import utils

pytest.importorskip("openlineage.client")

from openlineage.client import OpenLineageClient  # noqa: E402
from openlineage.client.transport.file import FileConfig, FileTransport  # noqa: E402

from hamilton.plugins import h_openlineage  # noqa: E402

REVENUE_QUERY = """
-- daily revenue per customer country
WITH paid AS (SELECT * FROM orders WHERE status = 'paid')
select p.order_date, c.country, p.amount
FROM paid p JOIN "customers" c ON p.customer_id = c.id
"""


def sqlite_metadata(path, query_or_table, results=1, schema=None):
    return utils.get_sql_metadata(
        query_or_table, results, db_connection=sqlite3.connect(path), schema=schema
    )


def identities(datasets):
    return sorted((d.namespace, d.name) for d in datasets)


@pytest.mark.parametrize(
    ("query", "tables"),
    [
        ("SELECT * FROM orders", ["orders"]),
        ("select o.id from orders o join customers c on o.cid = c.id", ["customers", "orders"]),
        (REVENUE_QUERY, ["customers", "orders"]),  # CTE `paid` and aliases are not tables
        ('/* leading */ SeLeCt id FrOm "Orders"', ["Orders"]),
        ("SELECT * FROM (SELECT * FROM orders) sub", ["orders"]),
    ],
)
def test_sql_datasets_sqlite_queries(tmp_path, query, tables):
    path = tmp_path / "sales.db"
    result = h_openlineage.sql_datasets(sqlite_metadata(path, query))
    assert result.notes == []
    assert result.outputs == []
    assert identities(result.inputs) == [(f"sqlite://{path.resolve()}", t) for t in tables]
    assert all(d.facets["dataSource"].uri == d.namespace for d in result.inputs)


POSTGRES_SOURCE = {
    "dialect": "postgresql",
    "host": "source.example",
    "port": None,
    "database": "sales",
    "default_schema": "public",
}


@pytest.mark.parametrize(
    ("query", "default_schema", "names", "note"),
    [
        (
            'SELECT * FROM Orders o JOIN "Customers" c ON o.cid = c.id JOIN sales.Reporting."Daily" d ON 1=1',
            "public",
            ["sales.public.Customers", "sales.public.orders", "sales.reporting.Daily"],
            None,
        ),
        ("SELECT * FROM orders", None, [], "cannot be fully qualified"),
        ("SELECT * FROM archive.orders", None, ["sales.archive.orders"], None),
    ],
)
def test_sql_datasets_postgres_naming_without_a_server(query, default_schema, names, note):
    """Folding, quoting and schema precedence are pure functions of the metadata."""
    metadata = {
        "sql_metadata": {
            "query": query,
            "source": {**POSTGRES_SOURCE, "default_schema": default_schema},
        }
    }
    result = h_openlineage.sql_datasets(metadata)
    assert identities(result.inputs) == [("postgres://source.example:5432", n) for n in names]
    assert (note is None and result.notes == []) or any(note in n for n in result.notes)


def test_sql_datasets_writer_schema_applies_to_every_dialect(tmp_path):
    postgres = {
        "sql_metadata": {
            "table_name": "daily_revenue",
            "schema": "reporting",
            "operation": "write",
            "source": POSTGRES_SOURCE,
        }
    }
    assert identities(h_openlineage.sql_datasets(postgres).outputs) == [
        ("postgres://source.example:5432", "sales.reporting.daily_revenue")
    ]
    sqlite = sqlite_metadata(tmp_path / "a.db", "daily_revenue", results=1, schema="reporting")
    assert identities(h_openlineage.sql_datasets(sqlite).outputs) == [
        (f"sqlite://{(tmp_path / 'a.db').resolve()}", "reporting.daily_revenue")
    ]


def test_sql_datasets_identity_agreement_and_distinction(tmp_path):
    a, b = tmp_path / "a.db", tmp_path / "b.db"
    written = h_openlineage.sql_datasets(sqlite_metadata(a, "daily_revenue", results=5))
    read = h_openlineage.sql_datasets(sqlite_metadata(a, "SELECT * FROM daily_revenue"))
    assert written.inputs == [] and read.outputs == []
    assert identities(written.outputs) == identities(read.inputs)
    other_db = h_openlineage.sql_datasets(sqlite_metadata(b, "daily_revenue", results=5))
    assert identities(other_db.outputs) != identities(written.outputs)


def test_sql_datasets_accepts_inner_dict_and_operation_override(tmp_path):
    metadata = sqlite_metadata(tmp_path / "a.db", "orders", results=pd.DataFrame({"x": [1]}))
    assert metadata["sql_metadata"]["operation"] == "read"
    inner = metadata["sql_metadata"]
    assert h_openlineage.sql_datasets(inner).inputs
    assert h_openlineage.sql_datasets(inner, operation="write").outputs


@pytest.mark.parametrize(
    ("metadata", "note"),
    [
        (utils.get_sql_metadata("orders", 5), "No connection supplied"),
        (utils.get_sql_metadata("SELECT * FROM orders", 5), "No connection supplied"),
        ({"sql_metadata": {"query": "SELECT * FROM orders", "table_name": None}}, "unknown"),
        (
            {"sql_metadata": {"rows": 1, "query": None, "table_name": None, "source": None}},
            "unknown",
        ),
        (
            {
                "sql_metadata": {
                    "table_name": "orders",
                    "source": {"dialect": "sqlite", "database": "/x.db"},
                }
            },
            "Operation for table 'orders' is unknown",
        ),
        (
            {
                "sql_metadata": {
                    "table_name": "orders",
                    "operation": "write",
                    "source": {"dialect": "mysql"},
                }
            },
            "No OpenLineage dataset naming for dialect 'mysql'",
        ),
        (
            utils.get_sql_metadata(
                "daily_revenue", 5, db_connection="postgresql://u:p@h/analytics"
            ),
            "cannot be fully qualified",
        ),
        (
            utils.get_sql_metadata("SELECT * FROM orders", 5, db_connection="postgresql:///sales"),
            "host is unknown",
        ),
        (
            {
                "sql_metadata": {
                    "query": "orders where",
                    "source": {"dialect": "sqlite", "database": "/x.db"},
                }
            },
            "SQL parsing error",
        ),
    ],
)
def test_sql_datasets_incomplete_metadata_is_diagnosed_not_guessed(metadata, note):
    result = h_openlineage.sql_datasets(metadata)
    assert result.inputs == [] and result.outputs == []
    assert any(note in n for n in result.notes), result.notes


def test_sql_datasets_parser_unavailable_or_failing(tmp_path, monkeypatch):
    metadata = sqlite_metadata(tmp_path / "a.db", "SELECT * FROM orders")
    monkeypatch.setitem(__import__("sys").modules, "openlineage_sql", None)
    missing = h_openlineage.sql_datasets(metadata)
    assert missing.inputs == [] and "openlineage-sql is not installed" in missing.notes[0]
    monkeypatch.undo()

    import openlineage_sql

    def boom(*args, **kwargs):
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(openlineage_sql, "parse", boom)
    failed = h_openlineage.sql_datasets(metadata)
    assert failed.inputs == [] and failed.notes == ["SQL parsing failed: RuntimeError"]


def revenue_module(query=REVENUE_QUERY):
    @load_from.sql(query_or_table=value(query), db_connection=source("sales_db"))
    def order_lines(df: pd.DataFrame) -> pd.DataFrame:
        return df

    def daily_revenue(order_lines: pd.DataFrame) -> pd.DataFrame:
        return order_lines.groupby(["order_date", "country"], as_index=False)["amount"].sum()

    @save_to.sql(
        table_name=source("revenue_table"),
        db_connection=source("warehouse_db"),
        schema=source("revenue_schema"),
        if_exists=value("replace"),
        index=value(False),
        output_name_="saved_revenue",
    )
    def revenue_report(daily_revenue: pd.DataFrame) -> pd.DataFrame:
        return daily_revenue

    return ad_hoc_utils.create_temporary_module(order_lines, daily_revenue, revenue_report)


def seed_sales(connection, schema=None):
    prefix = f"{schema}." if schema else ""
    pd.DataFrame(
        {
            "customer_id": [1, 1, 2],
            "order_date": ["d1", "d1", "d2"],
            "amount": [10.0, 5.0, 7.0],
            "status": ["paid", "paid", "open"],
        }
    ).to_sql("orders", connection, schema=schema, index=False, if_exists="replace")
    pd.DataFrame({"id": [1, 2], "country": ["NL", "DE"]}).to_sql(
        "customers", connection, schema=schema, index=False, if_exists="replace"
    )
    return prefix


def run_with_lineage(tmp_path, namespace, inputs):
    events_path = tmp_path / f"events-{namespace}.json"
    client = OpenLineageClient(
        transport=FileTransport(FileConfig(log_file_path=str(events_path), append=True))
    )
    adapter = h_openlineage.OpenLineageAdapter(client, namespace, "revenue_job")
    dr = driver.Builder().with_modules(revenue_module()).with_adapters(adapter).build()
    result = dr.execute(["saved_revenue"], inputs=inputs)
    events = [json.loads(line) for line in events_path.read_text().splitlines() if line.strip()]
    return result, events


def dataset_ids(events, key):
    return sorted((d["namespace"], d["name"]) for e in events for d in e.get(key) or [])


def test_revenue_flow_sqlite_emits_datasource_lineage(tmp_path):
    sales_path, warehouse_path = tmp_path / "sales.db", tmp_path / "warehouse.db"
    sales = sqlite3.connect(sales_path)
    seed_sales(sales)
    warehouse = create_engine(f"sqlite:///{warehouse_path}")
    inputs = {
        "sales_db": sales,
        "warehouse_db": warehouse,
        "revenue_table": "daily_revenue",
        "revenue_schema": None,
    }
    result, events = run_with_lineage(tmp_path, "demo_namespace", inputs)

    written = pd.read_sql("SELECT * FROM daily_revenue", warehouse)
    assert written["amount"].tolist() == [15.0]
    assert result["saved_revenue"]["sql_metadata"]["rows"] == 1

    sales_ns = f"sqlite://{sales_path.resolve()}"
    assert dataset_ids(events, "inputs") == [(sales_ns, "customers"), (sales_ns, "orders")]
    assert dataset_ids(events, "outputs") == [
        (f"sqlite://{warehouse_path.resolve()}", "daily_revenue")
    ]
    assert {e["job"]["namespace"] for e in events} == {"demo_namespace"}
    assert {e["job"]["name"] for e in events} == {"revenue_job"}
    assert [e["eventType"] for e in events] == ["START", "RUNNING", "RUNNING", "COMPLETE"]
    running = [e for e in events if e["eventType"] == "RUNNING"]
    assert running[0]["job"]["facets"]["sql"]["query"] == REVENUE_QUERY
    output = running[1]["outputs"][0]
    assert output["facets"]["schema"]["fields"][0]["name"] == "order_date"
    assert output["facets"]["dataSource"]["uri"] == output["namespace"]

    # dataset identity comes from the datasource, not the job namespace
    _, other_events = run_with_lineage(tmp_path, "another_namespace", inputs)
    assert dataset_ids(other_events, "inputs") == dataset_ids(events, "inputs")
    assert dataset_ids(other_events, "outputs") == dataset_ids(events, "outputs")
    assert {e["job"]["namespace"] for e in other_events} == {"another_namespace"}
    sales.close()


def test_lineage_failures_do_not_interrupt_data_work(tmp_path, monkeypatch, caplog):
    sales = sqlite3.connect(tmp_path / "sales.db")
    seed_sales(sales)
    warehouse = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}")
    inputs = {
        "sales_db": sales,
        "warehouse_db": warehouse,
        "revenue_table": "r",
        "revenue_schema": None,
    }

    def boom(*args, **kwargs):
        raise RuntimeError("conversion exploded postgresql://alice:s3cret@db/x")

    monkeypatch.setattr(h_openlineage, "sql_datasets", boom)
    with caplog.at_level(logging.WARNING, logger="hamilton.plugins.h_openlineage"):
        result, events = run_with_lineage(tmp_path, "ns", inputs)
    assert result["saved_revenue"]["sql_metadata"]["rows"] == 1
    assert pd.read_sql("SELECT * FROM r", warehouse)["amount"].tolist() == [15.0]
    assert [e["eventType"] for e in events] == ["START", "RUNNING", "RUNNING", "COMPLETE"]
    assert dataset_ids(events, "inputs") == [] and dataset_ids(events, "outputs") == []
    assert "conversion failed" in caplog.text and "RuntimeError" in caplog.text
    monkeypatch.undo()

    # producer boundary: connection inspection fails, data still flows, notes are logged
    monkeypatch.setattr(utils, "_inspect_sql_source", boom)
    with caplog.at_level(logging.WARNING, logger="hamilton.plugins.h_openlineage"):
        result, events = run_with_lineage(tmp_path, "ns2", inputs)
    assert result["saved_revenue"]["sql_metadata"]["source"] is None
    assert "Could not inspect" in result["saved_revenue"]["sql_metadata"]["notes"]
    assert "s3cret" not in json.dumps(result["saved_revenue"]) + caplog.text
    assert dataset_ids(events, "outputs") == []
    monkeypatch.undo()

    # an actual SQL failure still fails the graph
    with pytest.raises(Exception, match="no such table"):
        run_with_lineage(tmp_path, "ns3", {**inputs, "sales_db": sqlite3.connect(":memory:")})
    sales.close()


def test_revenue_flow_postgres_names_server_database_schema(tmp_path, postgres_schema):
    engine, schema = postgres_schema
    seed_sales(engine, schema)
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA {schema}_reporting"))
    try:
        query = REVENUE_QUERY.replace("FROM orders", f"FROM {schema}.orders").replace(
            '"customers"', f'{schema}."customers"'
        )
        module = revenue_module(query)
        events_path = tmp_path / "events.json"
        client = OpenLineageClient(
            transport=FileTransport(FileConfig(log_file_path=str(events_path), append=True))
        )
        adapter = h_openlineage.OpenLineageAdapter(client, "job_ns", "revenue_job")
        dr = driver.Builder().with_modules(module).with_adapters(adapter).build()
        with engine.connect() as warehouse_conn:
            dr.execute(
                ["saved_revenue"],
                inputs={
                    "sales_db": engine,
                    "warehouse_db": warehouse_conn,
                    "revenue_table": "daily_revenue",
                    "revenue_schema": f"{schema}_reporting",
                },
            )
            warehouse_conn.commit()
        events_text = events_path.read_text()
        events = [json.loads(line) for line in events_text.splitlines() if line.strip()]
        namespace = f"postgres://{engine.url.host}:{engine.url.port or 5432}"
        db = engine.url.database
        assert dataset_ids(events, "inputs") == [
            (namespace, f"{db}.{schema}.customers"),
            (namespace, f"{db}.{schema}.orders"),
        ]
        assert dataset_ids(events, "outputs") == [
            (namespace, f"{db}.{schema}_reporting.daily_revenue")
        ]
        assert engine.url.password not in events_text
        assert "job_ns" not in json.dumps(dataset_ids(events, "inputs"))

        # a later read of the report resolves to the identity it was written under
        read_back = utils.get_sql_metadata(
            f"SELECT * FROM {schema}_reporting.daily_revenue", pd.DataFrame(), db_connection=engine
        )
        assert identities(h_openlineage.sql_datasets(read_back).inputs) == dataset_ids(
            events, "outputs"
        )
        # unqualified names use the connection's verified default schema; folding matches the server
        default = utils.get_sql_metadata(
            "SELECT * FROM Daily_Revenue", pd.DataFrame(), db_connection=engine
        )
        with engine.connect() as conn:
            current = conn.execute(text("select current_schema()")).scalar()
        assert identities(h_openlineage.sql_datasets(default).inputs) == [
            (namespace, f"{db}.{current}.daily_revenue")
        ]
    finally:
        with engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA {schema}_reporting CASCADE"))
