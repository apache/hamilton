===============
Materialization
===============

So far, we executed our dataflow using the ``Driver.execute()`` method, which can receive an ``inputs`` dictionary and return a ``results`` dictionary (by default). However, you can also execute code with ``Driver.materialize()`` to directly read from / write to external data sources (file, database, cloud data store).

On this page, you'll learn:

- How to load and save data in Apache Hamilton
- Why use materialization
- What are ``DataSaver`` and ``DataLoader`` objects
- The difference between ``.execute()`` and ``.materialize()``
- The basics to write your own materializer

Different ways to write the same dataflow
-----------------------------------------

Below are 6 ways to write a dataflow that:

1. loads a dataframe from a parquet file
2. preprocesses the dataframe
3. trains a machine learning model
4. saves the trained model

The first two options don't use the concept of materialization and the next four do.

Without materialization
-----------------------

.. table::
   :align: left

   +----------------------------------------------+-----------------------------------------------+
   | 1) From nodes                                | 2) From ``Driver``                            |
   +==============================================+===============================================+
   | .. literalinclude:: _snippets/node_ctx.py    | .. literalinclude:: _snippets/driver_ctx.py   |
   |                                              |                                               |
   +----------------------------------------------+-----------------------------------------------+
   | .. image:: _snippets/node_ctx.png            | .. image:: _snippets/driver_ctx.png           |
   |    :width: 500px                             |    :width: 500px                              |
   +----------------------------------------------+-----------------------------------------------+

Observations:

1. These two approaches load and save data using ``pandas`` and ``xgboost`` without any Apache Hamilton constructs. These methods are transparent and simple to get started, but as the number of node grows (or across projects) defining one node per parquet file to load introduces a lot of boilerplate.
2. Using **1) from nodes** improves visibility by including loading & saving  in the dataflow (as illustrated).
3. Using **2) from ``Driver``** facilitates modifying loading & saving before code execution when executing the code, without modifying the dataflow itself. It is particularly useful when moving from development to production.

Limitations
~~~~~~~~~~~~

Apache Hamilton's approach to "materializations" aims to solve 3 limitations:

1. **Redundancy**: deduplicate loading & saving code to improve maintainability and debugging
2. **Observability**: include loading & saving in the dataflow for full observability and allow hooks
3. **Flexibility**: change the loading & saving behavior without editing the dataflow


With materialization
--------------------

.. table::
   :align: left

   +-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------+
   | 3) Simple Materialization                                   | 4) Static materializers                                     | 5) Dynamic materializers                                    | 6) Function modifiers                           |
   +=============================================================+=============================================================+=============================================================+=================================================+
   | .. literalinclude:: _snippets/simple_materializer_ctx.py    | .. literalinclude:: _snippets/static_materializer_ctx.py    | .. literalinclude:: _snippets/dynamic_materializer_ctx.py   | .. literalinclude:: _snippets/decorator_ctx.py  |
   |                                                             |                                                             |                                                             |                                                 |
   +-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------+
   | .. image:: _snippets/simple_materializer_ctx.png            | .. image:: _snippets/static_materializer_ctx.png            | .. image:: _snippets/dynamic_materializer_ctx.png           | .. image:: _snippets/decorator_ctx.png          |
   |    :width: 500px                                            |    :width: 500px                                            |    :width: 500px                                            |    :width: 500px                                |
   +-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------------------+-------------------------------------------------+

Simple Materialization
~~~~~~~~~~~~~~~~~~~~~~~
When you don't need to hide the implementation details of how you read and write, but you
want to track what was read and written, you need to expose extra metadata. This is where
the :doc:`@datasaver() <../reference/decorators/datasaver/>` and :doc:`@dataloader() <../reference/decorators/dataloader/>` decorators come in. They allow you to return
metadata about what was read and written, and this metadata is then used to track what
was read and written.

This is our recommended first step when you're starting to use materialization in Apache Hamilton.


Static materializers
~~~~~~~~~~~~~~~~~~~~

Passing ``from_`` and ``to`` Apache Hamilton objects to ``Builder().with_materializers()`` injects into the dataflow standardized nodes to load and save data. It solves the 3 limitations highlighted in the previous section:

1. Redundancy ✅: Using the ``from_`` and ``to`` Apache Hamilton constructs reduces the boilerplate to load and save data from common formats (JSON, parquet, CSV, etc.) and to interact with 3rd party libraries (pandas, matplotlib, xgboost, dlt, etc.)
2. Observability ✅: Loaders and savers are part of the dataflow. You can view them with ``Driver.display_all_functions()`` and execute nodes by requesting them with ``Driver.execute()``.
3. Flexibility ✅: The loading and saving behavior is decoupled from the dataflow and can modified easily when creating the ``Driver`` and executing code.

.. note::

    ``from_`` data loaders can be specified as optional with ``optional=True``. This allows specified data loaders to be skipped rather than raise an exception when not referenced by a dataflow.

Dynamic materializers
~~~~~~~~~~~~~~~~~~~~~

The dataflow is executed by passing ``from_`` and ``to`` objects to ``Driver.materialize()`` instead of the regular ``Driver.execute()``. This approach ressembles **2) from Driver**:

.. note::

   ``Driver.materialize()`` can receive data savers (``from_``) and loaders (``to``) and will execute all ``to`` passed. Like ``Driver.execute()``, it can receive ``inputs``, and ``overrides``, but instead of ``final_vars`` it receives ``additional_vars``.

1. Redundancy ✅: Uses ``from_`` and ``to`` Apache Hamilton constructs.
2. Observability 🚸: Materializers are visible with ``Driver.visualize_materialization()``, but can't be introspected otherwise. Also, you need to rely on ``Driver.materialize()`` which has a different call signature.
3. Flexibility ✅: Loading and saving is decoupled from the dataflow.

.. note::

   Using static materializers is typically preferrable. Static and dynamic materializers can be used together with ``dr = Builder.with_materializers().build()`` and later ``dr.materialize()``.

Function modifiers
~~~~~~~~~~~~~~~~~~

By adding ``@load_from`` and ``@save_to`` function modifiers (:ref:`loader-saver-decorators`) to Hamilton functions, materializers are generated when using ``Builder.with_modules()``. This approach ressembles **1) from Driver**:

.. note::

   Under the hood, the ``@load_from`` modifier uses the same code as ``from_`` to load data, same for ``@save_to`` and ``to``.

1. Redundancy 🚸: Using ``@load_from`` and ``@save_to`` reduces redundancy. However, to make available to multiple nodes a loaded table, you would need to decorate each node with the same ``@save_to``. Also, it might be impractical to decorate dynamically generated nodes (e.g., when using the ``@parameterize`` function modifier).
2. Observability ✅: Loaders and savers are part of the dataflow.
3. Flexibility 🚸: You can modify the path and materializer kwargs at runtime using ``source()`` in the decorator definition, but you can't change the format itself (e.g., from parquet to CSV).

.. note::

   It can be desirable to couple loading and saving to the dataflow using function modifiers. It makes it clear when reading the dataflow definition which nodes should load or save data using external sources.


DataLoader and DataSaver
------------------------

In Apache Hamilton, ``DataLoader`` and ``DataSaver`` are classes that define how to load or save a particular data format. Calling ``Driver.materialize(DataLoader(), DataSaver())`` adds nodes to the dataflow (see visualizations above).

Here are simplified snippets for saving and loading an XGBoost model to/from JSON.

   +----------------------------------------------+-----------------------------------------------+
   | DataLoader                                   | DataSaver                                     |
   +==============================================+===============================================+
   | .. literalinclude:: _snippets/data_loader.py | .. literalinclude:: _snippets/data_saver.py   |
   |                                              |                                               |
   +----------------------------------------------+-----------------------------------------------+

To define your own DataSaver and DataLoader, the Apache Hamilton `XGBoost extension <https://github.com/apache/hamilton/blob/main/hamilton/plugins/xgboost_extensions.py>`_ provides a good example


.. _sql-metadata-and-lineage:

SQL metadata and lineage
------------------------

The built-in SQL materializers (``@load_from.sql``, ``@save_to.sql``, ``from_.sql``, ``to.sql`` and the
``PandasSqlReader`` / ``PandasSqlWriter`` behind them) return ``sql_metadata`` describing what was read
or written. Since version ``1.1.0`` of that metadata, they also record *where*: the database the
connection points at. Lineage consumers such as the :doc:`OpenLineage adapter
<../reference/lifecycle-hooks/OpenLineageAdapter>` use this to name the physical tables a query
reads, without any custom loader or hand-maintained mapping.

Take a graph that reads a query joining ``orders`` and ``customers`` from a sales database,
aggregates daily revenue in Python, and writes ``daily_revenue`` to a reporting database:

.. code-block:: python

    @load_from.sql(query_or_table=value(REVENUE_QUERY), db_connection=source("sales_db"))
    def order_lines(df: pd.DataFrame) -> pd.DataFrame:
        return df

    @save_to.sql(table_name=value("daily_revenue"), schema=value("reporting"),
                 db_connection=source("warehouse_db"), output_name_="saved_revenue")
    def daily_revenue(order_lines: pd.DataFrame) -> pd.DataFrame:
        ...

With metadata version ``1.0.0``, the loader's metadata was ``{"rows": 3, "query": "...", "table_name": None}``: no table, no
server, no database. A join reported no inputs at all, and the saver's ``daily_revenue`` could not
be told apart from a table of the same name elsewhere. With version ``1.1.0``, the same code, with the same
connections, yields:

.. code-block:: python

    {"sql_metadata": {
        "rows": 3,
        "query": "WITH paid AS (...) SELECT ... FROM paid p JOIN customers c ON ...",
        "table_name": None,
        "schema": None,
        "operation": "read",
        "source": {"dialect": "postgresql", "host": "source.example", "port": 5432,
                   "database": "sales", "default_schema": "public"},
        "notes": "",
        "timestamp": 1758470400.0,
        "__version__": "1.1.0",
    }}

and the OpenLineage adapter, with ``sql_dataset_identity="datasource"`` (see
:ref:`sql-dataset-identity-change`), reports ``sales.public.orders`` and ``sales.public.customers`` under
``postgres://source.example:5432`` as inputs, and ``analytics.reporting.daily_revenue`` under the
warehouse's namespace as output. The same module produces the same identities whether it runs from
a script, a notebook or an orchestrator.

Fields
~~~~~~

The ``sql_metadata`` entry holds the following keys:

.. list-table::
   :header-rows: 1
   :widths: 18 82

   * - Key
     - Meaning
   * - ``rows``
     - Rows read (``len`` of the DataFrame) or the row count the write returned; ``None`` when unknown.
   * - ``query``
     - The statement executed, or ``None`` when a bare table name was read or written. As in 1.0.0,
       a string containing the upper-case text ``SELECT`` anywhere is filed here, and anything else
       under ``table_name``. Since 1.1.0 a read that starts (after comments) with ``select`` or
       ``with`` in any case is also filed here; 1.0.0 recorded a lower-case ``select ...`` as a table
       name. Writes and the two-argument form of :func:`~hamilton.io.utils.get_sql_metadata` keep the
       1.0.0 rule. Lineage consumers should use ``operation``: the string a write names is the table
       written, whichever of the two keys holds it (``"USER_SELECTIONS"`` is filed under ``query``).
       A written name that is not a plain identifier (``daily revenue``, ``SELECT results``) is
       parsed with ``openlineage-sql``: a statement that names tables contributes the tables it
       writes (or is left out, with a note, if it writes none), and a string naming no table is the
       table name. Without ``openlineage-sql``, such a name is left out of lineage with a note.
   * - ``table_name``
     - The bare table name read or written, or ``None`` for a statement.
   * - ``schema``
     - The schema explicitly passed to the writer (``PandasSqlWriter(schema=...)``), else ``None``.
       *New in 1.1.0.*
   * - ``operation``
     - ``"read"`` or ``"write"``; ``None`` when the helper was called in its original two-argument
       form and the direction is unknown. *New in 1.1.0.*
   * - ``source``
     - The datasource, or ``None`` when it could not be identified. It holds ``dialect``, the SQLAlchemy
       backend name (``postgresql`` or ``sqlite``); ``host``; ``port``; ``database``, which is the
       absolute file path for SQLite; and ``default_schema``, the schema unqualified names resolve
       against. ``default_schema`` is set only when SQLAlchemy already established it on the connection,
       and is ``None`` otherwise. SQLite sources also hold ``attached``, a mapping of attached database
       name to absolute file path, or ``None`` when the attached databases cannot be known (see
       below). *New in 1.1.0.*
   * - ``notes``
     - Why ``source`` is ``None``, for example ``"In-memory SQLite database has no stable identity"``
       or ``"Unsupported connection type for SQL metadata: MyConn"``; empty otherwise. *New in 1.1.0.*
   * - ``timestamp``
     - When the metadata was produced (POSIX seconds).
   * - ``__version__``
     - ``"1.1.0"``. Added keys bump the minor version; a change to an existing key's meaning bumps the
       major version.

Supported connections
~~~~~~~~~~~~~~~~~~~~~

The connection object determines what ``source`` can hold:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Connection passed as ``db_connection``
     - What ``source`` holds
   * - SQLAlchemy ``Engine`` or ``Connection`` (PostgreSQL, SQLite)
     - dialect, host, port, database from the URL; ``default_schema`` as SQLAlchemy determined it on
       connect (PostgreSQL ``current_schema()``).
   * - SQLAlchemy URL string (``"postgresql+psycopg2://..."``, ``"sqlite:///path.db"``)
     - dialect, host, port, database from the parsed URL; ``default_schema`` is ``None`` because pandas
       discards the temporary engine it built.
   * - Standard-library ``sqlite3.Connection`` on a file
     - ``dialect="sqlite"``, ``database`` = absolute file path, and ``attached`` = the file of every
       database attached to it, read with ``PRAGMA database_list`` on that same connection (no
       transaction is started). Only this connection form can see attached databases; for the others
       ``attached`` is ``None``.
   * - In-memory SQLite (``:memory:``, ``sqlite://``, ``sqlite:///:memory:``)
     - ``None`` with a note: two unrelated in-memory databases must not share an identity. A raw
       ``sqlite3`` in-memory connection with files attached keeps ``database=""`` and ``attached``, so
       tables in the attached files can still be named.
   * - Anything else (other DBAPI connections, mocks, and similar objects)
     - ``None`` with a note naming the type. Data loading and saving are unaffected.

Inspection never opens a connection, runs a write, commits, rolls back, or changes session settings,
and never raises: a failure during inspection becomes a ``notes`` entry naming the exception type
only. ``source`` holds scalars, never the connection object or the URL string, so it serializes
with ``json.dumps`` and cannot carry a username, password or URL query parameter. The ``query``
field is the SQL text you supplied, as before: keep secrets out of literals or strip them
downstream.

Schema precedence and unknown cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table referenced by a statement is qualified from, in order: the qualification written in the
SQL (``sales.public.orders``), the ``schema`` argument given to the writer, then ``source["default_schema"]``.
For SQLite, a schema names a database file rather than a namespace inside one: ``main`` (or no
schema) is the connection's file, and an attached database's tables are named in that file's
namespace, resolved through ``source["attached"]``. When the attached file cannot be known (a URL
or SQLAlchemy connection), or the schema is ``temp``, the table is left out rather than
attributed to the main file.
The default schema is what SQLAlchemy read from the server, not an assumption that PostgreSQL uses
``public``; when the connection's ``search_path`` spans several schemas, qualify table names in
the SQL to remove the ambiguity. When no schema can be determined, the table is left out of
lineage and the reason is reported. Only ``SELECT``-style statements pandas can execute are in
scope; SQL run inside ordinary Python functions is not observed.

Call the helper yourself
~~~~~~~~~~~~~~~~~~~~~~~~

Custom ``@dataloader`` / ``@datasaver`` functions can produce the same metadata:

.. code-block:: python

    from hamilton.io import utils

    @dataloader()
    def orders(sales_db: Engine) -> tuple[pd.DataFrame, dict]:
        query = "SELECT * FROM sales.public.orders"
        df = pd.read_sql(query, sales_db)
        return df, utils.get_sql_metadata(query, df, db_connection=sales_db, operation="read")

Pass ``operation="write"`` from a saver so the table name is never mistaken for a statement.
The original two-argument call ``get_sql_metadata(query_or_table, results)`` keeps working and
keeps its keys, their values and row-count semantics; it simply reports ``source=None`` with a note and
``operation=None``, so consumers diagnose it as incomplete rather than guessing.
