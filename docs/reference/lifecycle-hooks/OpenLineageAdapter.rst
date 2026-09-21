========================================
plugins.h_openlineage.OpenLineageAdapter
========================================

Install with ``pip install "apache-hamilton[openlineage]"``. The extra brings ``openlineage-python``
(the client) and, on Linux and macOS, ``openlineage-sql`` (the parser used to find the tables a
query reads). ``openlineage-sql`` publishes no Windows wheel, so the extra skips it there and SQL
queries are reported without table datasets on Windows.

.. autoclass:: hamilton.plugins.h_openlineage.OpenLineageAdapter
   :special-members: __init__
   :members:
   :inherited-members:

SQL datasets
------------

SQL loaders and savers (``@load_from.sql``, ``@save_to.sql`` and the pandas SQL materializers) record
the datasource they used (see :ref:`sql-metadata-and-lineage`). The adapter turns that into
OpenLineage datasets named after the datasource, following the `OpenLineage naming conventions
<https://openlineage.io/docs/spec/naming/>`_, and reports every physical table a query reads:

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
     - ``{table}``, or ``{schema}.{table}`` when the SQL or the writer names an attached database
       (no convention exists upstream; Hamilton defines this one)

Aliases and common table expressions are not reported as tables. Each dataset carries a
``dataSource`` facet with the namespace; the ``schema`` facet from ``dataframe_metadata`` is attached
only when the node maps to a single table. The job keeps the ``sql`` facet with the query text.

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

Dataset identity change
~~~~~~~~~~~~~~~~~~~~~~~

Before the datasource metadata existed, SQL datasets were emitted under the adapter's *job*
namespace with the bare ``table_name`` (queries produced a dataset with no name). Since metadata
version ``1.1.0``, they are emitted under the datasource namespace with a qualified name, so a lineage backend will show the
new datasets as different from the historical ones; no history is rewritten. Loaders and savers
whose metadata has no ``source`` (custom functions using the two-argument helper, in-memory
databases) no longer emit a job-scoped dataset. To keep the previous identities, pin the previous
Hamilton version.

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
