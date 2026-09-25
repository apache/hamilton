========================================
plugins.h_openlineage.OpenLineageAdapter
========================================

Install with ``pip install "apache-hamilton[openlineage]"``. The extra brings ``openlineage-python``
(the client) and, on Linux and macOS, ``openlineage-sql`` (the parser used to find the tables a
query reads). ``openlineage-sql`` publishes no Windows wheel, so the extra skips it there and SQL
queries, and written table names that are not plain identifiers, are reported without table
datasets on Windows. The parser is used only with
``sql_dataset_identity="datasource"``; the default identity needs neither it nor anything else
beyond the client.

.. autoclass:: hamilton.plugins.h_openlineage.OpenLineageAdapter
   :special-members: __init__
   :members:
   :inherited-members:

SQL datasets
------------

SQL loaders and savers (``@load_from.sql``, ``@save_to.sql`` and the pandas SQL materializers) record
the datasource they used (see :ref:`sql-metadata-and-lineage`). How the adapter names their datasets
is set by ``sql_dataset_identity``:

- ``"legacy"``, the default: datasets are named as in earlier Hamilton releases, under the adapter's
  *job* namespace with the bare ``table_name``. As before, a query read containing ``SELECT``
  produces a dataset with no name and the query in the job's ``sql`` facet, and other strings are
  used as the dataset name. Leaving the option unset warns once per adapter (a
  ``FutureWarning``) because the default will change; pass ``"legacy"`` explicitly to keep these names
  without the warning.
- ``"datasource"``: datasets are named after the datasource, following the `OpenLineage naming
  conventions <https://openlineage.io/docs/spec/naming/>`_, and every physical table a query reads is
  reported. A report written by one job and read by another then resolves to the same dataset, and
  two tables with the same name in different databases stay distinct.

.. code-block:: python

    adapter = OpenLineageAdapter(client, "my_namespace", "my_job", sql_dataset_identity="datasource")

The rest of this section describes the ``"datasource"`` identity:

.. list-table::
   :header-rows: 1
   :widths: 15 35 50

   * - Dialect
     - Namespace
     - Name
   * - PostgreSQL
     - ``postgres://{host}:{port}`` (port defaults to 5432)
     - ``{database}.{schema}.{table}``; unquoted identifiers are folded to lower case, as the server does
   * - SQLite
     - ``sqlite://{absolute file path}``
     - ``{table}``. A table in an attached database (``reporting.orders`` in the SQL, or the writer's
       ``schema``) is named in the attached file's namespace, which is known only for a
       standard-library ``sqlite3`` connection; otherwise it is left out.

Aliases and common table expressions are not reported as tables. Each dataset carries a
``dataSource`` facet with the namespace; the ``schema`` facet from ``dataframe_metadata`` is
attached only when the node maps to a single table. The job keeps the ``sql`` facet with the
statement's text; a node that read or wrote a table by name has no statement to report. The
exception is a table read by a name that the metadata files as a query (one containing
``SELECT``, or whose first word is ``select`` or ``with``, such as ``SELECT_LOG`` or
``select-log``): it can't be told apart from a statement, so the name is reported as the job's
SQL and no input dataset is emitted for it. Give such tables plain names, or read them with a
query.

Whatever cannot be fully identified is left out and logged as a warning from the
``hamilton.plugins.h_openlineage`` logger, never guessed. The following cases are left out:

- an unknown datasource (in-memory SQLite, an unsupported connection object, legacy two-argument metadata)
- an unsupported dialect
- a table whose schema cannot be determined
- a statement ``openlineage-sql`` cannot parse
- a missing ``openlineage-sql`` install

A failure inside the conversion is logged with its exception type and the run event is still
emitted without datasets. The node itself has already succeeded and is never failed by lineage.

.. _sql-dataset-identity-change:

Migrating to the datasource identity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The default stays ``"legacy"`` for now and will become ``"datasource"`` in a future major release.
Switching changes every SQL dataset's namespace and name (for example from ``my_namespace`` +
``daily_revenue`` to ``postgres://warehouse.example:5432`` + ``analytics.reporting.daily_revenue``).
A lineage backend shows the new names as new datasets: history recorded under the old names does
not connect to them, and nothing is rewritten automatically. Some datasets also stop appearing:

- loaders and savers whose metadata has no ``source`` (custom functions using the two-argument
  helper, in-memory databases)
- any of the unidentifiable cases above, including every SQL query and every written table name
  that is not a plain identifier on Windows, where ``openlineage-sql`` is not installed

To migrate:

1. Install ``openlineage-sql`` where you run Hamilton. ``apache-hamilton[openlineage]`` includes it
   everywhere except Windows. Pin it in locked environments.
2. Run the pipeline once with ``sql_dataset_identity="datasource"`` against a test backend, or read
   the events with ``FileTransport``, and note the new namespace and name of each dataset. Check the
   ``hamilton.plugins.h_openlineage`` warnings for anything left out.
3. In your lineage backend, move what is keyed to the old names (ownership, tags, alerts, policies,
   saved queries) to the new ones, or link old and new datasets where the backend supports it.
4. Pass ``sql_dataset_identity="datasource"`` in production.

To stay on the current names, pass ``sql_dataset_identity="legacy"``. It silences the warning.

Reuse the conversion
--------------------

:func:`~hamilton.plugins.h_openlineage.sql_datasets` is the boundary another integration (an
orchestrator provider, a custom adapter) can call on metadata Hamilton produced, with no
``OpenLineageClient``, ``Driver`` or database connection involved:

.. code-block:: python

    from hamilton.plugins.h_openlineage import sql_datasets

    lineage = sql_datasets(node_result_metadata)   # the dict a SQL loader/saver returned
    lineage.inputs    # list[openlineage.client.event_v2.Dataset]
    lineage.outputs
    lineage.notes     # why anything was left out

.. autofunction:: hamilton.plugins.h_openlineage.sql_datasets

.. autoclass:: hamilton.plugins.h_openlineage.SqlDatasets
   :members:
