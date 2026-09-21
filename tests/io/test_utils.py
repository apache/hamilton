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
import pathlib
import sqlite3
import subprocess
import sys

import pandas as pd
import pytest
from sqlalchemy import create_engine

from hamilton.io.utils import SQL_METADATA, get_file_metadata, get_sql_metadata, get_sql_source


def test_get_sql_metadata():
    results = 5
    table = "foo"
    query = "SELECT foo FROM bar"
    df = pd.DataFrame({"foo": ["bar"]})
    metadata1 = get_sql_metadata(table, df)[SQL_METADATA]
    metadata2 = get_sql_metadata(query, results)[SQL_METADATA]
    metadata3 = get_sql_metadata(query, "foo")[SQL_METADATA]
    assert metadata1["table_name"] == table
    assert metadata1["rows"] == 1
    assert metadata2["query"] == query
    assert metadata2["rows"] == 5
    assert metadata3["rows"] is None
    # legacy two-argument form: datasource is unknown, never guessed
    for metadata in (metadata1, metadata2, metadata3):
        assert metadata["source"] is None
        assert metadata["operation"] is None
        assert metadata["notes"]
    # statements are recognised regardless of keyword case
    assert (
        get_sql_metadata("select foo from bar", 1)[SQL_METADATA]["query"] == "select foo from bar"
    )
    assert get_sql_metadata("select foo from bar", 1)[SQL_METADATA]["table_name"] is None


def test_get_sql_metadata_sqlite_connections(tmp_path: pathlib.Path):
    path = tmp_path / "sales.db"
    conn = sqlite3.connect(path)
    metadata = get_sql_metadata("orders", 3, db_connection=conn)[SQL_METADATA]
    assert metadata["operation"] == "write"
    assert metadata["source"] == {
        "dialect": "sqlite",
        "host": None,
        "port": None,
        "database": str(path.resolve()),
        "default_schema": None,
    }
    assert metadata["notes"] == ""
    assert conn.in_transaction is False  # inspection did not start a transaction

    engine = create_engine(f"sqlite:///{path}")
    with engine.connect() as sa_conn:
        read = get_sql_metadata("SELECT * FROM orders", pd.DataFrame(), db_connection=sa_conn)
    assert read[SQL_METADATA]["operation"] == "read"
    assert read[SQL_METADATA]["source"]["database"] == str(path.resolve())
    assert (
        get_sql_metadata("orders", 3, db_connection=engine)[SQL_METADATA]["source"]["dialect"]
        == "sqlite"
    )

    for memory in (
        sqlite3.connect(":memory:"),
        create_engine("sqlite://"),
        create_engine("sqlite:///:memory:"),
        "sqlite:///:memory:",
    ):
        metadata = get_sql_metadata("orders", 3, db_connection=memory)[SQL_METADATA]
        assert metadata["source"] is None, memory
        assert "In-memory" in metadata["notes"]


def test_get_sql_metadata_url_string_has_no_credentials():
    url = "postgresql+psycopg2://alice:s3cret-pw@db.example:6543/sales?sslmode=require&application_name=x"
    metadata = get_sql_metadata("daily_revenue", 10, db_connection=url, schema="reporting")
    assert metadata[SQL_METADATA]["source"] == {
        "dialect": "postgresql",
        "host": "db.example",
        "port": 6543,
        "database": "sales",
        "default_schema": None,
    }
    assert metadata[SQL_METADATA]["schema"] == "reporting"
    serialized = json.dumps(metadata)
    for secret in ("alice", "s3cret-pw", "sslmode", "application_name", url):
        assert secret not in serialized


class _Broken:
    @property
    def url(self):
        raise RuntimeError("postgresql://alice:s3cret-pw@db.example/sales")


@pytest.mark.parametrize(
    ("connection", "note"),
    [
        (object(), "Unsupported connection type for SQL metadata: object"),
        (_Broken(), "Could not inspect _Broken connection: RuntimeError"),
    ],
)
def test_get_sql_metadata_unknown_or_failing_connection(connection, note):
    metadata = get_sql_metadata("orders", 3, db_connection=connection)[SQL_METADATA]
    assert metadata["source"] is None
    assert metadata["notes"] == note  # exception text (which may hold a URL) is not copied
    assert metadata["rows"] == 3 and metadata["table_name"] == "orders"
    assert get_sql_source(connection) == (None, note)


def test_get_sql_metadata_is_serializable_without_openlineage(tmp_path: pathlib.Path):
    script = f"""
import json, sqlite3, sys
from hamilton.io import utils
md = utils.get_sql_metadata("SELECT * FROM orders", 1, db_connection=sqlite3.connect({str(tmp_path / "a.db")!r}))
json.dumps(md)
assert not any(m.startswith("openlineage") for m in sys.modules), "optional stack was imported"
"""
    subprocess.run([sys.executable, "-c", script], check=True)


def test_get_file_metadata(tmp_path: pathlib.Path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")
    metadata = get_file_metadata(file_path)
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["file_metadata"]["size"] > 0
    assert metadata["file_metadata"]["last_modified"] == file_path.stat().st_mtime
    assert metadata["file_metadata"]["timestamp"] is not None


def test_get_file_metadata_url_schema():
    url = "s3://bucket/key"
    metadata = get_file_metadata(url)
    assert metadata["file_metadata"]["path"] == url
    assert metadata["file_metadata"]["scheme"] == "s3"
