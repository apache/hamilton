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

import os
import re
import sqlite3
import time
from datetime import datetime
from os import PathLike
from pathlib import Path
from typing import Any, Literal
from urllib import parse

import pandas as pd

DATAFRAME_METADATA = "dataframe_metadata"
SQL_METADATA = "sql_metadata"
FILE_METADATA = "file_metadata"

SqlOperation = Literal["read", "write"]

_LEADING_WORD = re.compile(r"\w+")


def _leading_sql_word(text: str) -> str | None:
    """The first word of ``text`` after any SQL comments, lower-cased; ``None`` if there is none."""
    rest = text.lstrip()
    while rest.startswith(("--", "/*")):
        line_comment = rest.startswith("--")
        end = rest.find("\n" if line_comment else "*/", 2)
        if end < 0:
            return None
        rest = rest[end + (1 if line_comment else 2) :].lstrip()
    word = _LEADING_WORD.match(rest)
    return word.group().lower() if word else None


def _starts_with_select(text: str) -> bool:
    """Whether ``text`` begins, after any comments, with ``select`` or ``with`` in any case."""
    return _leading_sql_word(text) in ("select", "with")


def _is_query(query_or_table: str, operation: SqlOperation | None, legacy: bool) -> bool:
    """Whether ``query_or_table`` goes under ``query`` (else ``table_name``) in the metadata.

    Metadata 1.0.0 counted anything containing ``SELECT`` as a query. That rule is kept for the
    two-argument form and for writes (``operation`` says a write names a table); a read also counts
    a statement that starts with a lower-case ``select``/``with``, which 1.0.0 misfiled as a table.
    """
    if "SELECT" in query_or_table:
        return True
    return not legacy and operation != "write" and _starts_with_select(query_or_table)


def get_file_metadata(path: str | Path | PathLike) -> dict[str, Any]:
    """Gives metadata from loading a file.

    Note: we reserve the right to change this schema. So if you're using this come
    chat so that we can make sure we don't break your code.

    This includes:
    - the file size
    - the file path
    - the last modified time
    - the current time
    """
    if isinstance(path, Path):
        path = str(path)
    parsed = parse.urlparse(path)
    size = None
    scheme = parsed.scheme
    last_modified = time.time()
    timestamp = datetime.now().utcnow().timestamp()
    notes = f"File metadata is unsupported for scheme: {scheme} or path: {path} does not exist."

    # Check if the path is a local file path (Windows drive can be listed as a scheme)
    is_win_path = parsed.scheme and len(parsed.scheme) == 1 and parsed.scheme.isalpha()
    if (parsed.scheme == "" or is_win_path) and os.path.exists(path):
        size = os.path.getsize(path)
        last_modified = os.path.getmtime(path)
        notes = ""

    return {
        FILE_METADATA: {
            "size": size,
            "path": path,
            "last_modified": last_modified,
            "timestamp": timestamp,
            "scheme": scheme,
            "notes": notes,
            "__version__": "1.0.0",
        }
    }


def get_dataframe_metadata(df: pd.DataFrame) -> dict[str, Any]:
    """Gives metadata from loading a dataframe.

    Note: we reserve the right to change this schema. So if you're using this come
    chat so that we can make sure we don't break your code.

    This includes:
    - the number of rows
    - the number of columns
    - the column names
    - the data types
    """
    metadata = {"__version__": "1.0.0"}
    try:
        metadata["rows"] = len(df)
    except TypeError:
        metadata["rows"] = None

    try:
        metadata["columns"] = len(df.columns)
    except (AttributeError, TypeError):
        metadata["columns"] = None

    try:
        metadata["column_names"] = list(df.columns)
    except (AttributeError, TypeError):
        metadata["column_names"] = None

    try:
        metadata["datatypes"] = [str(t) for t in list(df.dtypes)]
    except (AttributeError, TypeError):
        metadata["datatypes"] = None
    return {DATAFRAME_METADATA: metadata}


def get_file_and_dataframe_metadata(path: str, df: pd.DataFrame) -> dict[str, Any]:
    """Gives metadata from loading a file and a dataframe.

    Note: we reserve the right to change this schema. So if you're using this come
    chat so that we can make sure we don't break your code.

    This includes:
        file_meta:
            - the file size
            - the file path
            - the last modified time
            - the current time
        dataframe_meta:
        - the number of rows
        - the number of columns
        - the column names
        - the data types
    """
    return {**get_file_metadata(path), **get_dataframe_metadata(df)}


def get_sql_source(db_connection: Any) -> tuple[dict[str, Any] | None, str]:
    """Describes the database a connection points at, without credentials or live objects.

    Supported forms: SQLAlchemy URL strings, ``Engine`` and ``Connection`` objects, and
    standard-library ``sqlite3`` connections. Inspection is read-only: it reads URL fields
    that are already in memory and, for a raw sqlite3 connection, runs ``PRAGMA database_list``
    on that same connection (no transaction is started).

    :return: ``(source, notes)``. ``source`` is ``None`` when the connection cannot be
        identified, and ``notes`` then says why. When present, ``source`` holds
        ``dialect`` (SQLAlchemy backend name, e.g. ``postgresql``, ``sqlite``), ``host``,
        ``port``, ``database`` (the absolute file path for SQLite) and ``default_schema``
        (the schema the connection resolves unqualified names against, when SQLAlchemy has
        already fetched it; ``None`` otherwise). SQLite sources also hold ``attached``: a
        mapping of attached database name to absolute file path for a raw sqlite3
        connection, or ``None`` when the attached databases cannot be known without opening
        a connection. Usernames, passwords and URL query parameters are never included.
    """
    kind = type(db_connection).__name__
    try:
        source = _inspect_sql_source(db_connection)
    except Exception as e:  # inspection must never break the data operation
        return None, f"Could not inspect {kind} connection: {type(e).__name__}"
    if source is None:
        return None, f"Unsupported connection type for SQL metadata: {kind}"
    if source["dialect"] == "sqlite" and not source["database"] and not source.get("attached"):
        return None, "In-memory SQLite database has no stable identity"
    return source, ""


def _inspect_sql_source(db_connection: Any) -> dict[str, Any] | None:
    if isinstance(db_connection, sqlite3.Connection):
        # (seq, name, file) per database; file is "" for :memory: and temp
        databases = db_connection.execute("PRAGMA database_list").fetchall()
        path = next(file for _, name, file in databases if name == "main")
        source = _sql_source("sqlite", None, None, path, None)
        source["attached"] = {
            name: os.path.abspath(file)
            for _, name, file in databases
            if name not in ("main", "temp") and file
        }
        return source
    if isinstance(db_connection, str):
        from sqlalchemy.engine import make_url

        url = make_url(db_connection)
        default_schema = None
    else:
        engine = getattr(db_connection, "engine", db_connection)  # a Connection knows its Engine
        url = getattr(engine, "url", None)
        if url is None:
            return None
        default_schema = getattr(
            getattr(db_connection, "dialect", None), "default_schema_name", None
        )
    return _sql_source(url.get_backend_name(), url.host, url.port, url.database, default_schema)


def _sql_source(
    dialect: str,
    host: str | None,
    port: int | None,
    database: str | None,
    default_schema: str | None,
) -> dict[str, Any]:
    if dialect == "sqlite":
        if database == ":memory:":
            database = ""  # "sqlite:///:memory:" is in-memory too; leave it unidentified
        elif database:
            database = os.path.abspath(database)
    return {
        "dialect": dialect,
        "host": host,
        "port": port,
        "database": database,
        "default_schema": default_schema,
        **({"attached": None} if dialect == "sqlite" else {}),
    }


def get_sql_metadata(
    query_or_table: str,
    results: int | pd.DataFrame | None,
    *,
    db_connection: Any = None,
    schema: str | None = None,
    operation: SqlOperation | None = None,
) -> dict[str, Any]:
    """Gives metadata from reading a SQL table or writing to SQL db.

    Note: we reserve the right to change this schema. So if you're using this come
    chat so that we can make sure we don't break your code.

    This includes:
    - the number of rows read, added, or to add.
    - the sql query (e.g., "SELECT foo FROM bar")
    - the table name (e.g., "bar")
    - the current time
    - with ``db_connection``: the datasource (see :func:`get_sql_source`) and the
      ``operation`` (``read`` for a query, ``write`` for a table target, ``None`` when
      the legacy two-argument form is used), so lineage consumers can qualify tables.

    :param query_or_table: the SQL executed, or the bare table name read or written.
    :param results: the resulting DataFrame, or the row count returned by the write (``None``
        when the write reports no count, e.g. with a custom pandas ``method``).
    :param db_connection: the connection the operation ran on. Optional; when omitted the
        datasource is unknown and ``notes`` says so.
    :param schema: the schema the table was explicitly written to, when the writer had one.
    :param operation: ``"write"`` when ``query_or_table`` is what was written to (a table name,
        or a statement for custom savers), so lineage consumers know which key holds the target;
        ``"read"`` when it was read with,
        e.g., ``pandas.read_sql``. Inferred from ``results`` when omitted and ``db_connection`` given.
    """
    is_query = _is_query(
        query_or_table, operation, legacy=operation is None and db_connection is None
    )
    if isinstance(results, int):
        rows = results
    elif isinstance(results, pd.DataFrame):
        rows = len(results)
    else:
        rows = None
    if db_connection is None:
        source, notes = None, "No connection supplied; SQL datasource is unknown"
    else:
        source, notes = get_sql_source(db_connection)
        if operation is None:
            # writers return a row count (or None); readers return a DataFrame or an iterator
            wrote = results is None or isinstance(results, int)
            operation = "write" if wrote and not is_query else "read"
    return {
        SQL_METADATA: {
            "rows": rows,
            "query": query_or_table if is_query else None,
            "table_name": None if is_query else query_or_table,
            "schema": schema,
            "operation": operation,
            "source": source,
            "notes": notes,
            "timestamp": datetime.now().utcnow().timestamp(),
            "__version__": "1.1.0",
        }
    }
