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
import warnings

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
    conn = sqlite3.connect(tmp_path / "a.db")
    conn.execute(f"ATTACH DATABASE '{tmp_path / 'reporting.db'}' AS reporting")
    sqlite = utils.get_sql_metadata(
        "daily_revenue", 1, db_connection=conn, schema="reporting", operation="write"
    )
    assert identities(h_openlineage.sql_datasets(sqlite).outputs) == [
        (f"sqlite://{(tmp_path / 'reporting.db').resolve()}", "daily_revenue")
    ]


def test_sql_datasets_sqlite_attached_databases(tmp_path):
    main_path, other_path = tmp_path / "main.db", tmp_path / "other.db"
    conn = sqlite3.connect(main_path)
    conn.execute(f"ATTACH DATABASE '{other_path}' AS Reporting")
    query = "SELECT * FROM reporting.orders JOIN main.customers ON 1=1 JOIN regions ON 1=1"
    metadata = utils.get_sql_metadata(query, pd.DataFrame(), db_connection=conn)
    result = h_openlineage.sql_datasets(metadata)
    main_ns, other_ns = f"sqlite://{main_path.resolve()}", f"sqlite://{other_path.resolve()}"
    assert identities(result.inputs) == [
        (main_ns, "customers"),
        (main_ns, "regions"),
        (other_ns, "orders"),
    ]
    assert result.notes == []

    # a URL names only the main file: attached tables are left out, never put in main's namespace
    via_url = utils.get_sql_metadata(query, pd.DataFrame(), db_connection=f"sqlite:///{main_path}")
    result = h_openlineage.sql_datasets(via_url)
    assert identities(result.inputs) == [(main_ns, "customers"), (main_ns, "regions")]
    assert any("Cannot tell which file SQLite database 'reporting'" in n for n in result.notes)

    upper = utils.get_sql_metadata(
        "SELECT * FROM MAIN.customers", pd.DataFrame(), db_connection=conn
    )
    assert identities(h_openlineage.sql_datasets(upper).inputs) == [(main_ns, "customers")]

    memory = sqlite3.connect(":memory:")
    memory.execute(f"ATTACH DATABASE '{other_path}' AS reporting")
    query = "SELECT * FROM reporting.orders JOIN scratch ON 1=1"
    result = h_openlineage.sql_datasets(
        utils.get_sql_metadata(query, pd.DataFrame(), db_connection=memory)
    )
    assert identities(result.inputs) == [(other_ns, "orders")]
    assert any("in-memory database" in n for n in result.notes)

    for query, note in [
        ("SELECT * FROM temp.scratch", "temporary database"),
        ("SELECT * FROM missing.orders", "'missing' for table 'orders' is not attached"),
    ]:
        metadata = utils.get_sql_metadata(query, pd.DataFrame(), db_connection=conn)
        result = h_openlineage.sql_datasets(metadata)
        assert result.inputs == [] and any(note in n for n in result.notes), result.notes


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
    assert missing.query == "SELECT * FROM orders"  # recorded as a read query: still the job's SQL
    monkeypatch.undo()

    import openlineage_sql

    def boom(*args, **kwargs):
        raise RuntimeError("parser exploded")

    monkeypatch.setattr(openlineage_sql, "parse", boom)
    failed = h_openlineage.sql_datasets(metadata)
    assert failed.inputs == [] and failed.notes == ["SQL parsing failed: RuntimeError"]
    assert failed.query == "SELECT * FROM orders"


def test_sql_datasets_recorded_read_query_naming_no_table_keeps_its_statement(tmp_path):
    result = h_openlineage.sql_datasets(sqlite_metadata(tmp_path / "a.db", "SELECT 1"))
    assert result.inputs == [] and result.query == "SELECT 1"


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


def run_with_lineage(
    tmp_path, namespace, inputs, module=None, final_vars=("saved_revenue",), **adapter_kwargs
):
    events_path = tmp_path / f"events-{namespace}.json"
    client = OpenLineageClient(
        transport=FileTransport(FileConfig(log_file_path=str(events_path), append=True))
    )
    adapter = h_openlineage.OpenLineageAdapter(client, namespace, "revenue_job", **adapter_kwargs)
    dr = driver.Builder().with_modules(module or revenue_module()).with_adapters(adapter).build()
    result = dr.execute(list(final_vars), inputs=inputs)
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
    result, events = run_with_lineage(
        tmp_path, "demo_namespace", inputs, sql_dataset_identity="datasource"
    )

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
    _, other_events = run_with_lineage(
        tmp_path, "another_namespace", inputs, sql_dataset_identity="datasource"
    )
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
        result, events = run_with_lineage(tmp_path, "ns", inputs, sql_dataset_identity="datasource")
    assert result["saved_revenue"]["sql_metadata"]["rows"] == 1
    assert pd.read_sql("SELECT * FROM r", warehouse)["amount"].tolist() == [15.0]
    assert [e["eventType"] for e in events] == ["START", "RUNNING", "RUNNING", "COMPLETE"]
    assert dataset_ids(events, "inputs") == [] and dataset_ids(events, "outputs") == []
    assert "conversion failed" in caplog.text and "RuntimeError" in caplog.text
    monkeypatch.undo()

    # producer boundary: connection inspection fails, data still flows, notes are logged
    monkeypatch.setattr(utils, "_inspect_sql_source", boom)
    with caplog.at_level(logging.WARNING, logger="hamilton.plugins.h_openlineage"):
        result, events = run_with_lineage(
            tmp_path, "ns2", inputs, sql_dataset_identity="datasource"
        )
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
        adapter = h_openlineage.OpenLineageAdapter(
            client, "job_ns", "revenue_job", sql_dataset_identity="datasource"
        )
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
        # the password may be an ordinary word found in event tags, so look for it as a credential
        assert f":{engine.url.password}@" not in events_text
        assert engine.url.render_as_string(hide_password=False) not in events_text
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


def legacy_inputs(tmp_path):
    sales = sqlite3.connect(tmp_path / "sales.db")
    seed_sales(sales)
    return {
        "sales_db": sales,
        "warehouse_db": create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}"),
        "revenue_table": "daily_revenue",
        "revenue_schema": None,
    }


# string columns are "str" on pandas 3 and "object" before it; the facet records what pandas reports
STRING_DTYPE = str(pd.Series(["x"]).dtype)
REVENUE_FIELDS = [
    {"fields": [], "name": "order_date", "type": STRING_DTYPE},
    {"fields": [], "name": "country", "type": STRING_DTYPE},
    {"fields": [], "name": "amount", "type": "float64"},
]


def strip_private(value):
    """Drops the client-generated ``_producer``/``_schemaURL`` keys from an event fragment."""
    if isinstance(value, dict):
        return {k: strip_private(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [strip_private(v) for v in value]
    return value


def test_default_adapter_keeps_legacy_sql_identity(tmp_path, monkeypatch):
    """Pinned against the apache/main adapter: job namespace, bare table name, SQL job facet."""
    monkeypatch.setitem(__import__("sys").modules, "openlineage_sql", None)  # not needed
    with pytest.warns(FutureWarning, match="sql_dataset_identity='datasource'"):
        _, events = run_with_lineage(tmp_path, "demo_namespace", legacy_inputs(tmp_path))
    read, write = (strip_private(e) for e in events if e["eventType"] == "RUNNING")
    # a query read had no table name in metadata 1.0.0, so the dataset has none
    assert read["inputs"] == [
        {
            "namespace": "demo_namespace",
            "facets": {"schema": {"fields": REVENUE_FIELDS}},
            "inputFacets": {},
        }
    ]
    assert read["job"]["facets"] == {"sql": {"query": REVENUE_QUERY}}
    assert write["outputs"] == [
        {
            "namespace": "demo_namespace",
            "name": "daily_revenue",
            "facets": {"schema": {"fields": REVENUE_FIELDS}},
            "outputFacets": {},
        }
    ]
    assert write["job"]["facets"] == {}


def test_default_adapter_keeps_legacy_names_for_unusual_sql_strings(tmp_path):
    """Pinned against the apache/main adapter, which filed names by ``"SELECT" in text``."""

    @load_from.sql(query_or_table=value("select * from orders"), db_connection=source("sales_db"))
    def lower_query(df: pd.DataFrame) -> pd.DataFrame:
        return df

    @save_to.sql(
        table_name=value("USER_SELECTIONS"),
        db_connection=source("warehouse_db"),
        if_exists=value("replace"),
        index=value(False),
        output_name_="saved_selections",
    )
    def selections(lower_query: pd.DataFrame) -> pd.DataFrame:
        return lower_query

    module = ad_hoc_utils.create_temporary_module(lower_query, selections)
    with pytest.warns(FutureWarning):
        _, events = run_with_lineage(
            tmp_path,
            "demo_namespace",
            legacy_inputs(tmp_path),
            module=module,
            final_vars=["saved_selections"],
        )
    read, write = (strip_private(e) for e in events if e["eventType"] == "RUNNING")
    assert [(d["namespace"], d.get("name")) for d in read["inputs"]] == [
        ("demo_namespace", "select * from orders")
    ]
    assert read["job"]["facets"] == {"sql": {}}
    # 1.0.0 filed a name containing SELECT as a query, so the legacy dataset has no name
    assert [(d["namespace"], d.get("name")) for d in write["outputs"]] == [("demo_namespace", None)]


@pytest.mark.parametrize(
    ("sql_metadata", "name", "query"),
    [
        # hand-built by custom loaders (as in earlier versions of examples/openlineage)
        (
            {"query": "SELECT * FROM orders", "table_name": "orders"},
            "orders",
            "SELECT * FROM orders",
        ),
        ({"query": None, "table_name": "SELECT_LOG"}, "SELECT_LOG", None),
        ({"query": "SELECT * FROM orders", "table_name": None}, None, "SELECT * FROM orders"),
        ({"query": "select * from orders", "table_name": None}, None, "select * from orders"),
        # 1.1.0 filing of a lower-case read; 1.0.0 filed (and named) it as a table
        (
            {"query": "select * from orders", "table_name": None, "__version__": "1.1.0"},
            "select * from orders",
            None,
        ),
    ],
)
def test_legacy_dataset_helpers_match_1_0_0(sql_metadata, name, query):
    """Pinned against apache/main's create_input_dataset / create_output_dataset."""
    metadata = {"sql_metadata": sql_metadata}
    inputs, sql_facet = h_openlineage.create_input_dataset("ns", metadata, None)
    (output,) = h_openlineage.create_output_dataset("ns", metadata, None)
    assert [(d.namespace, d.name) for d in inputs] == [("ns", name)]
    assert (output.namespace, output.name) == ("ns", name)
    assert sql_facet.query == query


def test_default_adapter_legacy_table_read(tmp_path):
    @load_from.sql(query_or_table=value("customers"), db_connection=source("sales_url"))
    def customers(df: pd.DataFrame) -> pd.DataFrame:
        return df

    seed_sales(sqlite3.connect(tmp_path / "sales.db"))
    module = ad_hoc_utils.create_temporary_module(customers)
    events_path = tmp_path / "events.json"
    client = OpenLineageClient(
        transport=FileTransport(FileConfig(log_file_path=str(events_path), append=True))
    )
    adapter = h_openlineage.OpenLineageAdapter(client, "demo_namespace", "job")
    dr = driver.Builder().with_modules(module).with_adapters(adapter).build()
    with pytest.warns(FutureWarning):
        dr.execute(["customers"], inputs={"sales_url": f"sqlite:///{tmp_path / 'sales.db'}"})
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    (read,) = (strip_private(e) for e in events if e["eventType"] == "RUNNING")
    assert [(d["namespace"], d["name"]) for d in read["inputs"]] == [
        ("demo_namespace", "customers")
    ]
    assert read["job"]["facets"] == {"sql": {}}  # the 1.0.0 facet for a table read has no query


def test_legacy_identity_warning_fires_once_and_only_by_default(tmp_path, recwarn):
    run_with_lineage(tmp_path, "ns_default", legacy_inputs(tmp_path))
    identity_warnings = [w for w in recwarn.list if "sql_dataset_identity" in str(w.message)]
    assert [w.category for w in identity_warnings] == [FutureWarning]  # two SQL nodes, one warning
    message = str(identity_warnings[0].message)
    assert "sql_dataset_identity='legacy'" in message and "OpenLineageAdapter/" in message
    recwarn.clear()
    for identity in ("legacy", "datasource"):
        run_with_lineage(
            tmp_path, f"ns_{identity}", legacy_inputs(tmp_path), sql_dataset_identity=identity
        )
    assert not [w for w in recwarn.list if "sql_dataset_identity" in str(w.message)]


def test_legacy_identity_warning_as_error_does_not_fail_the_node(tmp_path, caplog):
    with warnings.catch_warnings():
        warnings.simplefilter("error", FutureWarning)
        with caplog.at_level(logging.WARNING, logger="hamilton.plugins.h_openlineage"):
            result, events = run_with_lineage(tmp_path, "ns", legacy_inputs(tmp_path))
    assert result["saved_revenue"]["sql_metadata"]["rows"] == 1
    assert dataset_ids(events, "outputs") == [("ns", "daily_revenue")]
    assert "legacy identity" in caplog.text


def test_legacy_identity_conversion_failure_does_not_fail_the_node(tmp_path, monkeypatch, caplog):
    def boom(*args, **kwargs):
        raise RuntimeError("legacy conversion exploded")

    monkeypatch.setattr(h_openlineage, "create_output_dataset", boom)
    with caplog.at_level(logging.WARNING, logger="hamilton.plugins.h_openlineage"):
        result, events = run_with_lineage(
            tmp_path, "ns", legacy_inputs(tmp_path), sql_dataset_identity="legacy"
        )
    assert result["saved_revenue"]["sql_metadata"]["rows"] == 1
    assert dataset_ids(events, "outputs") == []
    assert "conversion failed" in caplog.text


def test_invalid_sql_dataset_identity_fails_at_construction():
    with pytest.raises(ValueError, match="sql_dataset_identity must be one of"):
        h_openlineage.OpenLineageAdapter(None, "ns", "job", sql_dataset_identity="qualified")


@pytest.mark.parametrize(
    ("table", "query", "table_name"),
    [
        ("daily revenue", None, "daily revenue"),
        ("SELECTED_ROWS", "SELECTED_ROWS", None),
        ("SELECT results", "SELECT results", None),
    ],
)
def test_written_table_names_are_emitted_as_tables(tmp_path, table, query, table_name):
    inputs = {**legacy_inputs(tmp_path), "revenue_table": table}
    result, events = run_with_lineage(tmp_path, "ns", inputs, sql_dataset_identity="datasource")
    metadata = result["saved_revenue"]["sql_metadata"]
    # the 1.0.0 query/table_name filing is kept; operation marks the name as the table written
    assert (metadata["query"], metadata["table_name"], metadata["operation"]) == (
        query,
        table_name,
        "write",
    )
    assert dataset_ids(events, "outputs") == [
        (f"sqlite://{(tmp_path / 'warehouse.db').resolve()}", table)
    ]
    (write,) = (e for e in events if e["eventType"] == "RUNNING" and e.get("outputs"))
    assert "sql" not in write["job"]["facets"]  # a table name is not the job's SQL


def test_read_by_a_non_plain_table_name_reports_no_statement(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'a.db'}")
    pd.DataFrame({"x": [1]}).to_sql("daily revenue", engine, index=False)
    metadata = utils.get_sql_metadata(
        "daily revenue", pd.DataFrame(), db_connection=engine, operation="read"
    )
    result = h_openlineage.sql_datasets(metadata)
    assert result.inputs == [] and result.notes  # not guessed
    assert result.query is None  # a table name is not the job's SQL


@pytest.mark.parametrize("parser", ["missing", "failing"])
def test_sql_datasets_written_name_without_parser(tmp_path, monkeypatch, parser):
    if parser == "missing":
        monkeypatch.setitem(__import__("sys").modules, "openlineage_sql", None)
    else:
        import openlineage_sql

        def boom(*args, **kwargs):
            raise RuntimeError("parser exploded")

        monkeypatch.setattr(openlineage_sql, "parse", boom)
    conn = sqlite3.connect(tmp_path / "a.db")

    def written(name):
        metadata = utils.get_sql_metadata(name, 3, db_connection=conn, operation="write")
        return h_openlineage.sql_datasets(metadata)

    assert identities(written("USER_SELECTIONS").outputs) == [
        (f"sqlite://{(tmp_path / 'a.db').resolve()}", "USER_SELECTIONS")
    ]
    # a table name and a statement can't be told apart without a parse: left out, explained
    for ambiguous in (
        "SELECT results",
        "daily revenue",
        "INSERT INTO t SELECT * FROM s",
        "TRUNCATE t; INSERT INTO t SELECT * FROM s",
        "(SELECT * FROM s)",
    ):
        result = written(ambiguous)
        assert result.outputs == [] and result.notes, ambiguous


@pytest.mark.parametrize(
    ("statement", "inputs", "outputs"),
    [
        ("INSERT INTO t SELECT * FROM s", ["s"], ["t"]),
        ("CREATE TABLE t AS SELECT a FROM s", ["s"], ["t"]),
        ("TRUNCATE t; INSERT INTO t SELECT * FROM s", ["s"], ["t"]),
        ("insert into t select * from s", ["s"], ["t"]),  # filed under table_name
    ],
)
def test_sql_datasets_write_statements_are_parsed(tmp_path, statement, inputs, outputs):
    """A custom saver recording the statement it ran gets the tables, not the SQL as a name."""
    metadata = sqlite_metadata(tmp_path / "a.db", statement, results=3)
    ns = f"sqlite://{(tmp_path / 'a.db').resolve()}"
    result = h_openlineage.sql_datasets(metadata, operation="write")
    assert identities(result.outputs) == [(ns, t) for t in outputs]
    assert identities(result.inputs) == [(ns, t) for t in inputs]
    assert result.query == statement


def test_sql_datasets_write_of_a_pure_query_is_left_out(tmp_path):
    metadata = sqlite_metadata(tmp_path / "a.db", "SELECT * FROM s", results=3)
    result = h_openlineage.sql_datasets(metadata, operation="write")
    assert result.outputs == [] and result.inputs == []
    assert result.notes == ["Write metadata holds a statement that writes no table"]


@pytest.mark.parametrize(
    ("query", "tables"),
    [("(select * from orders)", ["orders"]), ("pragma table_info(orders)", [])],
)
def test_read_strings_that_are_not_names_are_parsed_not_named(tmp_path, query, tables):
    """1.0.0 files these under table_name; they must not become a dataset named after the SQL."""
    metadata = sqlite_metadata(tmp_path / "a.db", query, results=pd.DataFrame())
    assert metadata["sql_metadata"]["table_name"] == query
    result = h_openlineage.sql_datasets(metadata)
    # reported as the job's SQL only when the parse shows it is a statement naming tables
    assert result.query == (query if tables else None)
    assert identities(result.inputs) == [
        (f"sqlite://{(tmp_path / 'a.db').resolve()}", t) for t in tables
    ]
    assert tables or result.notes


def test_attached_sqlite_database_is_attributed_to_its_own_file(tmp_path):
    main_path, other_path = tmp_path / "main.db", tmp_path / "other.db"
    seed_sales(sqlite3.connect(other_path))
    conn = sqlite3.connect(main_path)
    conn.execute(f"ATTACH DATABASE '{other_path}' AS reporting")

    @load_from.sql(
        query_or_table=value("SELECT * FROM reporting.orders"), db_connection=source("db")
    )
    def orders(df: pd.DataFrame) -> pd.DataFrame:
        return df

    events_path = tmp_path / "events.json"
    client = OpenLineageClient(
        transport=FileTransport(FileConfig(log_file_path=str(events_path), append=True))
    )
    adapter = h_openlineage.OpenLineageAdapter(
        client, "ns", "job", sql_dataset_identity="datasource"
    )
    module = ad_hoc_utils.create_temporary_module(orders)
    dr = driver.Builder().with_modules(module).with_adapters(adapter).build()
    dr.execute(["orders"], inputs={"db": conn})
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    assert dataset_ids(events, "inputs") == [(f"sqlite://{other_path.resolve()}", "orders")]
