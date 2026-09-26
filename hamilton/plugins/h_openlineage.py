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

import dataclasses
import json
import logging
import re
import sys
import traceback
import warnings
from datetime import datetime, timezone
from typing import Any, Literal, NamedTuple, get_args

import attr
from openlineage.client import OpenLineageClient, event_v2, facet_v2

from hamilton import graph as h_graph
from hamilton import graph_types, node
from hamilton.io.utils import SQL_METADATA, SqlOperation
from hamilton.lifecycle import base

logger = logging.getLogger(__name__)

SqlDatasetIdentity = Literal["legacy", "datasource"]
_SQL_DATASET_IDENTITIES = get_args(SqlDatasetIdentity)


@attr.s
class HamiltonFacet(facet_v2.RunFacet):
    """Class for Hamilton Facet."""

    hamilton_run_id: str = attr.ib()
    graph_version: str = attr.ib()
    final_vars: list[str] = attr.ib()
    inputs: list[str] = attr.ib()
    overrides: list[str] = attr.ib()


def get_stack_trace(exception):
    # Python changed this API in 3.10
    if sys.version_info < (3, 10, 0):
        return traceback.format_exception(
            etype=type(exception), value=exception, tb=exception.__traceback__
        )

    return "".join(traceback.format_exception(exception))


def extract_schema_facet(metadata):
    """Extracts the schema facet from the metadata."""
    if "dataframe_metadata" in metadata:
        schema_datatypes = [
            facet_v2.schema_dataset.SchemaDatasetFacetFields(
                name=k,
                type=v,
            )
            for k, v in zip(
                metadata["dataframe_metadata"]["column_names"],
                metadata["dataframe_metadata"]["datatypes"],
                strict=False,
            )
        ]
        schema_facet = facet_v2.schema_dataset.SchemaDatasetFacet(
            fields=schema_datatypes,
        )
        return schema_facet
    return None


@dataclasses.dataclass
class SqlDatasets:
    """Datasets resolved from Hamilton SQL metadata. ``notes`` explains anything left out.

    ``query`` is the SQL statement the metadata recorded, or ``None`` when it named a table (a
    written name may be filed under the metadata's ``query``) or cannot be told apart from one. A
    table read by a name the metadata files as a query (one containing ``SELECT``, or whose first
    word after comments is ``select`` or ``with`` in any case) cannot be told apart from a
    statement, so its name is reported here and no input dataset is emitted for it.
    """

    inputs: list[event_v2.Dataset]
    outputs: list[event_v2.Dataset]
    notes: list[str]
    query: str | None = None


class _Dialect(NamedTuple):
    parser: str  # openlineage-sql dialect name
    scheme: str  # OpenLineage namespace scheme
    folds_unquoted: bool  # server lower-cases unquoted identifiers
    default_port: int | None = None


# an unquoted, optionally qualified identifier
_PLAIN_NAME = re.compile(r"[\w$]+(\.[\w$]+)*")

# keyed by SQLAlchemy backend name
_DIALECTS = {
    "postgresql": _Dialect("postgres", "postgres", True, 5432),
    "sqlite": _Dialect("sqlite", "sqlite", False),
}


def sql_datasets(
    sql_metadata: dict[str, Any], operation: SqlOperation | None = None
) -> SqlDatasets:
    """Converts Hamilton SQL metadata into OpenLineage datasets. Emits nothing, opens nothing.

    This is the reusable boundary for other integrations (e.g. an orchestrator provider):
    feed it the ``sql_metadata`` produced by :func:`hamilton.io.utils.get_sql_metadata` (either
    the whole metadata dict or its ``sql_metadata`` entry) and get datasets named per the
    `OpenLineage naming conventions <https://openlineage.io/docs/spec/naming/>`_:

    - PostgreSQL: namespace ``postgres://{host}:{port}``, name ``{database}.{schema}.{table}``.
      Unquoted identifiers are folded to lower case, as the server does.
    - SQLite: namespace ``sqlite://{absolute file path}``, name ``{table}``. A table in an
      attached database (``{schema}.{table}`` in the SQL, or the writer's ``schema``) is named
      in the attached file's namespace; it is left out when that file cannot be known.

    Queries are parsed with ``openlineage-sql``; every physical table read appears in ``inputs``
    and every table written in ``outputs`` (aliases and common table expressions are not tables).
    A bare table name is placed by ``operation`` (``read``/``write``), taken from the metadata
    unless given here. What a write names is its table when it is a plain identifier; otherwise it
    is parsed, and is the table written unless it parses as a statement that names tables (then the
    tables it writes are used, if any). Without a parse it is left out. A read string that is not a
    plain name is parsed as SQL rather than used as one. Schema precedence: explicit in the SQL,
    then the writer's ``schema``, then the connection's default schema. Anything that cannot be
    fully identified is left out and explained in ``notes`` rather than guessed — an unknown datasource, an unsupported
    dialect, a missing schema, a parse error or a missing ``openlineage-sql`` install.
    """
    md = sql_metadata.get(SQL_METADATA, sql_metadata)
    result = SqlDatasets([], [], [])
    source = md.get("source")
    if not source:
        result.notes.append(md.get("notes") or "SQL datasource is unknown; no dataset emitted")
        return result
    if source["dialect"] not in _DIALECTS:
        result.notes.append(f"No OpenLineage dataset naming for dialect {source['dialect']!r}")
        return result
    dialect = _DIALECTS[source["dialect"]]
    query, table_name = md.get("query"), md.get("table_name")
    operation = operation or md.get("operation")
    # what a write names may be under either key (1.0.0 files anything containing "SELECT" under
    # ``query``): a plain name is the table; anything else is parsed, and is the table written
    # unless it parses as a statement that names tables
    write_target = (query or table_name) if operation == "write" else None
    if write_target and _PLAIN_NAME.fullmatch(write_target):
        query, table_name = None, write_target
    elif write_target:
        query, table_name = write_target, None
    elif operation == "read" and table_name and not _PLAIN_NAME.fullmatch(table_name):
        # a read string that is not a plain name is SQL, whichever key it was filed under
        query, table_name = table_name, None

    def to_datasets(
        tables: list[tuple[str | None, str | None, str, bool]],
    ) -> list[event_v2.Dataset]:
        datasets = []
        for table in tables:
            dataset, note = _dataset(source, md.get("schema"), *table)
            if dataset:
                datasets.append(dataset)
            else:
                result.notes.append(note)
        return datasets

    if query:
        try:
            import openlineage_sql
        except ImportError:
            openlineage_sql = None
            note = "openlineage-sql is not installed; install apache-hamilton[openlineage] to resolve tables from SQL"
        parsed = None
        if openlineage_sql:
            try:
                parsed = openlineage_sql.parse([query], dialect=dialect.parser)
            except Exception as e:
                note = f"SQL parsing failed: {type(e).__name__}"
        # a statement, not a table name: filed as a read query, or parsed as naming tables
        recorded_as_query = not write_target and md.get("query") == query
        if recorded_as_query or (parsed and (parsed.out_tables or parsed.in_tables)):
            result.query = query
        if write_target and parsed and not parsed.out_tables:
            if parsed.in_tables:
                result.notes.append("Write metadata holds a statement that writes no table")
                return result
            # names no table at all, so it is not a statement: it is the name of the table written
            result.outputs = to_datasets([(None, None, write_target, True)])
            return result
        if parsed is None:  # without a parse a name and a statement can't be told apart
            result.notes.append(note)
            return result
        result.notes.extend(f"SQL parsing error: {err.message}" for err in parsed.errors)
        result.inputs = to_datasets(_parsed_tables(parsed.in_tables, dialect.folds_unquoted))
        result.outputs = to_datasets(_parsed_tables(parsed.out_tables, dialect.folds_unquoted))
    elif table_name:
        # a name pandas passed straight to the database: taken as written, no folding
        datasets = to_datasets([(None, None, table_name, True)])
        if operation == "read":
            result.inputs = datasets
        elif operation == "write":
            result.outputs = datasets
        else:
            result.notes.append(
                f"Operation for table {table_name!r} is unknown (legacy metadata); no dataset emitted"
            )
    else:
        result.notes.append("SQL metadata has neither a query nor a table name")
    return result


def _parsed_tables(
    tables: list[Any], folds: bool
) -> list[tuple[str | None, str | None, str, bool]]:
    """(database, schema, name, name_quoted) per parsed table, folding unquoted parts if asked."""

    def part(value, style, key):
        quoted = getattr(style, key, None) is not None
        return value.lower() if value and folds and not quoted else value

    return [
        (
            part(t.database, t.quote_style, "database"),
            part(t.schema, t.quote_style, "schema"),
            t.name,
            getattr(t.quote_style, "name", None) is not None,
        )
        for t in tables
    ]


def _dataset(
    source: dict[str, Any],
    explicit_schema: str | None,
    database: str | None,
    schema: str | None,
    name: str,
    quoted: bool,
) -> tuple[event_v2.Dataset | None, str]:
    """Names one table; returns (dataset, "") or (None, why not)."""
    dialect = _DIALECTS[source["dialect"]]
    if dialect.folds_unquoted and not quoted:
        name = name.lower()
    schema = schema or explicit_schema  # written in the SQL, else the writer's schema=
    if source["dialect"] == "sqlite":
        # a SQLite schema names a database file; the dataset lives in that file's namespace
        path, note = _sqlite_file(source, schema, name)
        if not path:
            return None, note
        namespace = f"{dialect.scheme}://{path}"
        full_name = name
    else:
        if not source["host"]:
            return None, f"{source['dialect']} host is unknown; cannot name {name!r}"
        namespace = f"{dialect.scheme}://{source['host']}:{source['port'] or dialect.default_port}"
        database = database or source["database"]
        schema = schema or source["default_schema"]
        if not database or not schema:
            return None, (
                f"Table {name!r} cannot be fully qualified (database={database!r}, schema={schema!r}); "
                "qualify it in the SQL, pass schema= to the writer, or use a SQLAlchemy Engine/Connection"
            )
        full_name = f"{database}.{schema}.{name}"
    facets = {
        "dataSource": facet_v2.datasource_dataset.DatasourceDatasetFacet(
            name=namespace, uri=namespace
        )
    }
    return event_v2.Dataset(namespace, full_name, facets=facets), ""


def _sqlite_file(source: dict[str, Any], schema: str | None, name: str) -> tuple[str | None, str]:
    """The file a SQLite table lives in; returns (path, "") or (None, why not)."""
    if not schema or schema.lower() == "main":
        if not source["database"]:
            return None, f"Table {name!r} is in an in-memory database, which has no stable identity"
        return source["database"], ""
    if schema.lower() == "temp":
        return None, f"Table {name!r} is in the temporary database, which has no stable identity"
    attached = source.get("attached")
    if attached is None:
        return None, (
            f"Cannot tell which file SQLite database {schema!r} is for table {name!r}; "
            "pass the sqlite3 connection the database was attached on"
        )
    # SQLite database names are case-insensitive
    path = {k.lower(): v for k, v in attached.items()}.get(schema.lower())
    if not path:
        return None, f"SQLite database {schema!r} for table {name!r} is not attached to a file"
    return path, ""


def _legacy_sql_fields(sql_metadata: dict[str, Any]) -> tuple[str | None, str | None]:
    """``(query, table_name)`` as metadata 1.0.0 filed them, which the legacy identity names from.

    1.1.0 files a read starting with a lower-case ``select``/``with`` under ``query``, where 1.0.0
    filed it (and so named the legacy dataset) under ``table_name``; only that case is moved back.
    Metadata without a newer ``__version__`` (e.g. built by hand) is used exactly as given.
    """
    query, table_name = sql_metadata.get("query"), sql_metadata.get("table_name")
    refiled = sql_metadata.get("__version__", "1.0.0") != "1.0.0"
    if refiled and query and table_name is None and "SELECT" not in query:
        return None, query
    return query, table_name


def create_input_dataset(
    namespace: str, metadata: dict, node_
) -> tuple[list[event_v2.InputDataset], facet_v2.sql_job.SQLJobFacet | None]:
    """Creates the open lineage input dataset, in the job namespace (legacy SQL identity)."""
    datasource_facet = None
    storage_facet = None
    sql_facet = None
    if "file_metadata" in metadata:
        name = node_.name
        if ".loader" in name:
            name = name.split(".loader")[0]
        path = metadata["file_metadata"]["path"]
        format = path.split(".")[-1] if "." in name else "unknown"
        storage_facet = facet_v2.storage_dataset.StorageDatasetFacet(
            storageLayer="FileSystem",
            fileFormat=format,
        )
        datasource_facet = facet_v2.datasource_dataset.DatasourceDatasetFacet(
            name=name,
            uri=path,
        )
    elif "sql_metadata" in metadata:
        query, name = _legacy_sql_fields(metadata["sql_metadata"])
        sql_facet = facet_v2.sql_job.SQLJobFacet(
            query=query,
        )
    else:
        name = "--UNKNOWN--"
    schema_facet = extract_schema_facet(metadata)
    inputFacets = {}
    if storage_facet:
        inputFacets["storage"] = storage_facet
    if datasource_facet:
        inputFacets["dataSource"] = datasource_facet
    if schema_facet:
        inputFacets["schema"] = schema_facet
    if len(inputFacets) == 0:
        inputFacets = None
    inputs = [event_v2.InputDataset(namespace, name, facets=inputFacets)]
    return inputs, sql_facet


def _sql_lineage(
    metadata: dict[str, Any], operation: SqlOperation, node_: node.Node
) -> tuple[list[event_v2.Dataset], str | None]:
    """Datasets and SQL statement for a SQL loader/saver node, named after the datasource."""
    lineage = sql_datasets(metadata, operation)
    for note in lineage.notes:
        logger.warning("OpenLineage SQL lineage for node %s is incomplete: %s", node_.name, note)
    datasets = lineage.inputs if operation == "read" else lineage.outputs
    schema_facet = extract_schema_facet(metadata) if len(datasets) == 1 else None
    if schema_facet:
        datasets[0].facets["schema"] = schema_facet
    return datasets, lineage.query


def create_output_dataset(namespace: str, metadata: dict, node_) -> list[event_v2.OutputDataset]:
    """Creates the open lineage output dataset, in the job namespace (legacy SQL identity)."""
    datasource_facet = None
    storage_facet = None
    if "file_metadata" in metadata:
        name = metadata["file_metadata"]["path"]
        format = name.split(".")[-1] if "." in name else "unknown"
        storage_facet = facet_v2.storage_dataset.StorageDatasetFacet(
            storageLayer="FileSystem",
            fileFormat=format,
        )
        datasource_facet = facet_v2.datasource_dataset.DatasourceDatasetFacet(
            name=node_.name,
            uri=name,
        )
    elif "sql_metadata" in metadata:
        _, name = _legacy_sql_fields(metadata["sql_metadata"])
    else:
        name = "--UNKNOWN--"
    schema_facet = extract_schema_facet(metadata)
    outputFacets = {}
    if storage_facet:
        outputFacets["storage"] = storage_facet
    if datasource_facet:
        outputFacets["dataSource"] = datasource_facet
    if schema_facet:
        outputFacets["schema"] = schema_facet
    if len(outputFacets) == 0:
        outputFacets = None
    outputs = [event_v2.OutputDataset(namespace, name, facets=outputFacets)]
    return outputs


class OpenLineageAdapter(
    base.BasePreGraphExecute,
    base.BasePreNodeExecute,
    base.BasePostNodeExecute,
    base.BasePostGraphExecute,
):
    """
    This adapter emits OpenLineage events.

    .. code-block:: python

        # create the openlineage client
        from openlineage.client import OpenLineageClient

        # write to file
        from openlineage.client.transport.file import FileConfig, FileTransport
        file_config = FileConfig(
            log_file_path="/path/to/your/file",
            append=False,
        )
        client = OpenLineageClient(transport=FileTransport(file_config))

        # write to HTTP, e.g. marquez
        client = OpenLineageClient(url="http://localhost:5000")

        # create the adapter
        adapter = OpenLineageAdapter(client, "my_namespace", "my_job_name")

        # add to Hamilton
        # import your pipeline code
        dr = driver.Builder().with_modules(YOUR_MODULES).with_adapters(adapter).build()
        # execute as normal -- and openlineage events will be emitted
        dr.execute(...)

    Note for data lineage to be emitted, you must use the "materializer" abstraction to provide
    metadata. See https://hamilton.apache.org/concepts/materialization/.
    This can be done via the `@datasaver()` and `@dataloader()` decorators, or
    using the `@load_from` or `@save_to` decorators, as well as passing in data savers
    and data loaders via `.with_materializers()` on the Driver Builder, or via `.materialize()`
    on the driver object.
    """

    def __init__(
        self,
        client: OpenLineageClient,
        namespace: str,
        job_name: str,
        sql_dataset_identity: SqlDatasetIdentity | None = None,
    ):
        """Constructor. You pass in the OLClient.

        :param self:
        :param client:
        :param namespace:
        :param job_name:
        :param sql_dataset_identity: how SQL loader/saver datasets are identified.
            ``"legacy"`` (the current default) names them ``namespace`` + bare table name, as
            earlier releases did. ``"datasource"`` names them after the database they live in,
            per the OpenLineage naming conventions (see :func:`sql_datasets`), so lineage
            connects across jobs. Leaving it unset uses ``"legacy"`` and warns once, since the
            default will change to ``"datasource"`` in a future major release.
        :return:
        """
        if sql_dataset_identity not in (None, *_SQL_DATASET_IDENTITIES):
            raise ValueError(
                f"sql_dataset_identity must be one of {_SQL_DATASET_IDENTITIES}, "
                f"got {sql_dataset_identity!r}"
            )
        # self.transport = transport
        self.client = client
        self.namespace = namespace
        self.job_name = job_name
        self.sql_dataset_identity: SqlDatasetIdentity = sql_dataset_identity or "legacy"
        self._warn_sql_identity_default = sql_dataset_identity is None

    def _warn_legacy_sql_identity(self):
        """Warns once per adapter that SQL datasets use the default legacy identity."""
        if not self._warn_sql_identity_default:
            return
        self._warn_sql_identity_default = False
        message = (
            "OpenLineageAdapter is naming SQL datasets with the legacy identity (job namespace + "
            "bare table name). A future major release will default to "
            "sql_dataset_identity='datasource', which names datasets after their database "
            "(e.g. postgres://host:5432 + db.schema.table) so lineage connects across jobs. "
            "Existing lineage history will not connect to the new names automatically. To keep "
            "the current names, pass sql_dataset_identity='legacy'. To migrate, pass "
            "sql_dataset_identity='datasource' and move anything keyed to the old names "
            "(ownership, tags, alerts, policies) in your lineage backend. See "
            "https://hamilton.apache.org/reference/lifecycle-hooks/OpenLineageAdapter/"
        )
        try:
            warnings.warn(message, FutureWarning, stacklevel=2)
        except Exception:  # warnings filtered to errors must not fail the node or drop lineage
            logger.warning(message)

    def pre_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        final_vars: list[str],
        inputs: dict[str, Any],
        overrides: dict[str, Any],
    ):
        """
        Emits a Run START event.
        Emits a Job Event with the sourceCode Facet for the entire DAG as the job.

        :param run_id:
        :param graph:
        :param final_vars:
        :param inputs:
        :param overrides:
        :return:
        """
        exportable_graph = graph_types.HamiltonGraph.from_graph(graph)
        graph_version = exportable_graph.version
        node_dict = [n.as_dict() for n in exportable_graph.nodes]
        job = event_v2.Job(
            namespace=self.namespace,
            name=self.job_name,
            facets={
                "sourceCode": facet_v2.source_code_job.SourceCodeJobFacet(
                    language="python",
                    sourceCode=json.dumps(node_dict),
                ),
                "jobType": facet_v2.job_type_job.JobTypeJobFacet(
                    processingType="BATCH",
                    integration="Hamilton",
                    jobType="DAG",
                ),
            },
        )
        run = event_v2.Run(
            runId=run_id,
            facets={
                "hamilton": HamiltonFacet(
                    hamilton_run_id=run_id,
                    graph_version=graph_version,
                    final_vars=final_vars,
                    inputs=list(inputs.keys()) if inputs else [],
                    overrides=list(overrides.keys()) if overrides else [],
                )
            },
        )
        run_event = event_v2.RunEvent(
            eventType=event_v2.RunState.START,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=run,
            job=job,
        )
        self.client.emit(run_event)

    def pre_node_execute(
        self, run_id: str, node_: node.Node, kwargs: dict[str, Any], task_id: str | None = None
    ):
        """No event emitted."""
        pass

    def post_node_execute(
        self,
        run_id: str,
        node_: node.Node,
        kwargs: dict[str, Any],
        success: bool,
        error: Exception | None,
        result: Any | None,
        task_id: str | None = None,
    ):
        """
        Run Event: will emit a RUNNING event with updates on input/outputs.

        A Job Event will be emitted for graph execution, and additional SQLJob facet if data was loaded
        from a SQL source.

        A Dataset Event will be emitted if a dataloader or datasaver was used:

           - input data set if loader
           - output data set if saver
           - appropriate facets will be added to the dataset where it makes sense.

        TODO: attach statistics facets

        :param run_id:
        :param node_:
        :param kwargs:
        :param success:
        :param error:
        :param result:
        :param task_id:
        :return:
        """
        if not success:
            # do not emit anything
            return
        metadata = {}
        saved_or_loaded = ""
        if node_.tags.get("hamilton.data_saver") is True and isinstance(result, dict):
            metadata = result
            saved_or_loaded = "saved"
        elif (
            node_.tags.get("hamilton.data_loader") is True
            and node_.tags.get("hamilton.data_loader.has_metadata") is True
            and isinstance(result, tuple)
            and len(result) == 2
            and isinstance(result[1], dict)
        ):
            metadata = result[1]
            saved_or_loaded = "loaded"
        if not metadata:
            # no metadata to emit
            return

        inputs = []
        outputs = []
        sql_facet = None
        try:
            if "sql_metadata" in metadata and self.sql_dataset_identity == "datasource":
                # SQL datasets are named after their datasource, not the job namespace
                operation: SqlOperation = "read" if saved_or_loaded == "loaded" else "write"
                sql_datasets_, query = _sql_lineage(metadata, operation, node_)
                datasets = [
                    (event_v2.InputDataset if operation == "read" else event_v2.OutputDataset)(
                        d.namespace, d.name, facets=d.facets
                    )
                    for d in sql_datasets_
                ]
                if operation == "read":
                    inputs = datasets
                else:
                    outputs = datasets
                if query:
                    sql_facet = facet_v2.sql_job.SQLJobFacet(query=query)
            else:
                if "sql_metadata" in metadata:
                    self._warn_legacy_sql_identity()
                if saved_or_loaded == "loaded":
                    inputs, sql_facet = create_input_dataset(self.namespace, metadata, node_)
                else:
                    outputs = create_output_dataset(self.namespace, metadata, node_)
        except Exception as e:  # lineage must never fail a node that already succeeded
            # only the exception type at WARNING: messages may quote connection details
            logger.warning(
                "OpenLineage dataset conversion failed for node %s in run %s (%s); emitting the "
                "run event without datasets",
                node_.name,
                run_id,
                type(e).__name__,
            )
            logger.debug("OpenLineage dataset conversion failure", exc_info=True)
            inputs, outputs, sql_facet = [], [], None

        run = event_v2.Run(
            runId=run_id,
        )
        job_facets = {}
        if sql_facet:
            job_facets["sql"] = sql_facet
        job = event_v2.Job(namespace=self.namespace, name=self.job_name, facets=job_facets)
        run_event = event_v2.RunEvent(
            eventType=event_v2.RunState.RUNNING,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=run,
            job=job,
            inputs=inputs,
            outputs=outputs,
        )
        self.client.emit(run_event)

    def post_graph_execute(
        self,
        run_id: str,
        graph: h_graph.FunctionGraph,
        success: bool,
        error: Exception | None,
        results: dict[str, Any] | None,
    ):
        """Emits a Run COMPLETE or FAIL event.

        :param run_id:
        :param graph:
        :param success:
        :param error:
        :param results:
        :return:
        """
        job = event_v2.Job(
            namespace=self.namespace,
            name=self.job_name,
        )
        facets = {}
        run_event_type = event_v2.RunState.COMPLETE
        if error:
            run_event_type = event_v2.RunState.FAIL
            error_message = str(error)
            facets = {
                "errorMessage": facet_v2.error_message_run.ErrorMessageRunFacet(
                    message=error_message,
                    stackTrace=get_stack_trace(error),
                    programmingLanguage="python",
                )
            }
        run = event_v2.Run(runId=run_id, facets=facets)

        run_event = event_v2.RunEvent(
            eventType=run_event_type,
            eventTime=datetime.now(timezone.utc).isoformat(),
            run=run,
            job=job,
        )
        self.client.emit(run_event)


# if __name__ == "__main__":
#     from openlineage.client import OpenLineageClient
#     from openlineage.client.transport.file import FileConfig, FileTransport
#
#     file_config = FileConfig(
#         log_file_path="/path/to/your/file",
#         append=False,
#     )
#
#     client = OpenLineageClient(transport=FileTransport(file_config))
#     namespace = "my_namespace"
#     db_datset = Dataset(namespace, name, facets)
