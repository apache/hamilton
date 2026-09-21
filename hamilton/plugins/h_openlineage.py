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
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, NamedTuple

import attr
from openlineage.client import OpenLineageClient, event_v2, facet_v2

from hamilton import graph as h_graph
from hamilton import graph_types, node
from hamilton.io.utils import SQL_METADATA, SqlOperation
from hamilton.lifecycle import base

logger = logging.getLogger(__name__)


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
    """Datasets resolved from Hamilton SQL metadata. ``notes`` explains anything left out."""

    inputs: list[event_v2.Dataset]
    outputs: list[event_v2.Dataset]
    notes: list[str]


class _Dialect(NamedTuple):
    parser: str  # openlineage-sql dialect name
    scheme: str  # OpenLineage namespace scheme
    folds_unquoted: bool  # server lower-cases unquoted identifiers
    default_port: int | None = None


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
    - SQLite: namespace ``sqlite://{absolute file path}``, name ``{table}``, or
      ``{schema}.{table}`` when the SQL or the writer names an attached database.

    Queries are parsed with ``openlineage-sql``; every physical table read appears in ``inputs``
    and every table written in ``outputs`` (aliases and common table expressions are not tables).
    A bare table name is placed by ``operation`` (``read``/``write``), taken from the metadata
    unless given here. Schema precedence: explicit in the SQL, then the writer's ``schema``,
    then the connection's default schema. Anything that cannot be fully identified is left out
    and explained in ``notes`` rather than guessed — an unknown datasource, an unsupported
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
            result.notes.append(
                "openlineage-sql is not installed; install apache-hamilton[openlineage] to resolve tables from SQL"
            )
            return result
        try:
            parsed = openlineage_sql.parse([query], dialect=dialect.parser)
        except Exception as e:
            result.notes.append(f"SQL parsing failed: {type(e).__name__}")
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
        namespace = f"{dialect.scheme}://{source['database']}"
        full_name = f"{schema}.{name}" if schema else name
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


def create_input_dataset(namespace: str, metadata: dict, node_) -> list[event_v2.InputDataset]:
    """Creates the open lineage input dataset for file (or unknown) metadata, in the job namespace."""
    datasource_facet = None
    storage_facet = None
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
    return [event_v2.InputDataset(namespace, name, facets=inputFacets)]


def _sql_lineage_datasets(
    metadata: dict[str, Any], operation: SqlOperation, node_: node.Node
) -> list[event_v2.Dataset]:
    """Datasets for a SQL loader/saver node; datasource namespaces, not the job namespace."""
    lineage = sql_datasets(metadata, operation)
    for note in lineage.notes:
        logger.warning("OpenLineage SQL lineage for node %s is incomplete: %s", node_.name, note)
    datasets = lineage.inputs if operation == "read" else lineage.outputs
    schema_facet = extract_schema_facet(metadata) if len(datasets) == 1 else None
    if schema_facet:
        datasets[0].facets["schema"] = schema_facet
    return datasets


def create_output_dataset(namespace: str, metadata: dict, node_) -> list[event_v2.OutputDataset]:
    """Creates the open lineage output dataset for file (or unknown) metadata, in the job namespace."""
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

    def __init__(self, client: OpenLineageClient, namespace: str, job_name: str):
        """Constructor. You pass in the OLClient.

        :param self:
        :param client:
        :param namespace:
        :param job_name:
        :return:
        """
        # self.transport = transport
        self.client = client
        self.namespace = namespace
        self.job_name = job_name

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

        inputs: list[event_v2.Dataset] = []
        outputs: list[event_v2.Dataset] = []
        sql_facet = None
        try:
            if "sql_metadata" in metadata:
                # SQL datasets are named after their datasource, not the job namespace
                operation: SqlOperation = "read" if saved_or_loaded == "loaded" else "write"
                datasets = _sql_lineage_datasets(metadata, operation, node_)
                if operation == "read":
                    inputs = datasets
                else:
                    outputs = datasets
                query = metadata["sql_metadata"].get("query")
                if query:
                    sql_facet = facet_v2.sql_job.SQLJobFacet(query=query)
            elif saved_or_loaded == "loaded":
                inputs = create_input_dataset(self.namespace, metadata, node_)
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
            inputs=[event_v2.InputDataset(d.namespace, d.name, facets=d.facets) for d in inputs],
            outputs=[event_v2.OutputDataset(d.namespace, d.name, facets=d.facets) for d in outputs],
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
