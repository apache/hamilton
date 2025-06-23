=========
Dagster
=========

Here are some code snippets to compare the macro orchestrator Dagster to the micro orchestrator Apache Hamilton. Apache Hamilton can run inside Dagster, but you wouldn't run Dagster inside Apache Hamilton.

While the two have different scope, there's a lot of overlap between the two both in terms of functionality and API. Indeed, Dagster's software-defined assets introduced in 2022 matches Apache Hamilton's declarative approach and should feel familiar to users of either.


------
TL;DR
------

.. list-table::
    :widths: 24 39 39
    :header-rows: 1

    * - Trait
      - Apache Hamilton
      - Dagster
    * - Declarative API
      - ✅
      - ✅
    * - Dependencies
      - Lightweight library with minimal dependencies (``numpy``, ``pandas``, ``typing_inspect``). Minimizes dependency conflicts.
      - Heavier framework/system with several dependencies (``pydantic``, ``sqlalchemy``, ``requests``, ``Jinja2``, ``protobuf``). ``urllib3`` on which depends ``requests`` introduced breaking changes several times and ``pydantic`` v1 and v2 are incompatible.
    * - Macro orchestration
      - DIY or in tandem with Dagster, Airflow, Prefect, Metaflow, etc.
      - Includes: manual, schedules, sensors, conditional execution
    * - Micro orchestration (i.e., ``dbt``, ``LangChain``)
      - Can run anywhere (locally, notebook, macro orchestrator, `FastAPI <https://hamilton.apache.org/integrations/fastapi/>`_, `Streamlit <https://hamilton.apache.org/integrations/streamlit/>`_, pyodide, etc.)
      - ❌
    * - Code structure
      - Since it's micro, there are no restrictions.
      - Since it's macro, a certain code structure is required to properly package code. The prevalent use of relative imports in the tutorial reduces code reusability.
    * - LLM applications
      - Well-suited for `LLM applications <https://blog.dagworks.io/p/retrieval-augmented-generation-reference-arch>`_ since it's a micro orchestration framework.
      - ❌
    * - Lineage
      - Fine-grained / column-level lineage. Includes `utilities to explore lineage <https://hamilton.apache.org/how-tos/use-hamilton-for-lineage/>`_.
      - Coarser operations to reduce orchestration and I/O overhead.
    * - Visualization
      - `View the dataflow and produce visual artifacts <https://hamilton.apache.org/concepts/visualization/>`_. Configurable and supports extensive custom styling.
      - Export Daster UI in ``.svg``. No styling.
    * - Run tracking
      - `DAGWorks <https://docs.dagworks.io/capabilities>`_ (premium)
      - Dagster UI
    * - Experiment Managers
      - Has an `experiment manager plugin <https://blog.dagworks.io/p/building-a-lightweight-experiment>`_
      - ❌
    * - Materializers
      - `Data Savers & Loaders <https://hamilton.apache.org/concepts/materialization/>`_
      - `IO Managers <https://docs.dagster.io/_apidocs/io-managers>`_
    * - Data validation
      - `Native validators and pandera plugin <https://hamilton.apache.org/how-tos/run-data-quality-checks/>`_
      - `Asset checks <https://docs.dagster.io/_apidocs/asset-checks>`_ (experimental), `pandera integration <https://docs.dagster.io/integrations/pandera>`_
    * - Versioning operations
      - Nodes and dataflow versions are derived from code.
      - `Asset code version <https://docs.dagster.io/concepts/assets/software-defined-assets#asset-code-versions>`_ is specified manually.
    * - Versioning data
      - Automated code version + data value are used to read from cache or compute new results with `DiskCacheAdapter <https://docs.dagster.io/concepts/assets/software-defined-assets#asset-code-versions>`_
      - Manual asset code version + upstream changes are used to `trigger re-materialization <https://docs.dagster.io/concepts/assets/software-defined-assets#asset-code-versions>`_
    * - In-memory Execution
      - Default
      - `Materialize in-memory <https://docs.dagster.io/_apidocs/io-managers>`_
    * - Task-based Execution
      - `TaskBasedExecutor <https://hamilton.apache.org/reference/drivers/Driver/#taskbasedgraphexecutor>`_
      - Default
    * - Dynamic branching
      - `Parallelizable/Collect <https://hamilton.apache.org/concepts/parallel-task/>`_
      - `Mapping/Collect <https://docs.dagster.io/_apidocs/dynamic>`_
    * - Hooks
      - `Lifecycle hooks <https://hamilton.apache.org/reference/lifecycle-hooks/>`_ (easier to extend)
      - `Op Hooks <https://docs.dagster.io/concepts/ops-jobs-graphs/op-hooks#op-hooks>`_
    * - Plugins
      - `Spark <https://blog.dagworks.io/p/expressing-pyspark-transformations>`_, Dask, Ray, `Datadog <https://hamilton.apache.org/reference/lifecycle-hooks/DDOGTracer/>`_, polars, pandera, and more (Apache Hamilton is less restrictive and easier to extend)
      - `Spark, Dask, polars, pandera, Databricks, Snowflake, Great Expections, and more <https://docs.dagster.io/integrations>`_  (Dagster integrations are more involved to develop)
    * - Interactive Development
      - `Jupyter Magic <https://hamilton.apache.org/how-tos/use-in-jupyter-notebook/#use-hamilton-jupyter-magic>`_, `VSCode extension <https://marketplace.visualstudio.com/items?itemName=ThierryJean.hamilton>`_
      - ❌


----------------------
Dataflow definition
----------------------

.. table:: HackerNews top stories
   :align: left

   +------------------------------------------------------------+----------------------------------------------------------+
   | Apache Hamilton                                            | Dagster                                                  |
   +============================================================+==========================================================+
   | .. literalinclude:: _dagster_snippets/hamilton_dataflow.py | .. literalinclude:: _dagster_snippets/dagster_dataflow.py| 
   |                                                            |                                                          |
   +------------------------------------------------------------+----------------------------------------------------------+
   | .. image:: _dagster_snippets/hamilton_dataflow.png         | .. image:: _dagster_snippets/dagster_dataflow.png        |
   |                                                            |                                                          |
   +------------------------------------------------------------+----------------------------------------------------------+

.. list-table:: Key points
    :widths: 24 39 39
    :header-rows: 1

    * - Trait
      - Apache Hamilton
      - Dagster
    * - Define operations
      - Uses the native Python function signature. The dataflow is assembled based on function/parameter names and type annotations.
      - Uses the ``@asset`` decorator to transform function in operations and specify dependencies by passing functions.
    * - Data I/O
      - Loading/Saving is decoupled from the dataflow definition. The code becomes `more portable and facilitates moving from dev to prod <https://blog.dagworks.io/p/separate-data-io-from-transformation>`_.
      - Each asset code operations is coupled with I/O. Hard-coding this behavior reduces maintainability.
    * - Lineage
      - Favors granular operations and fine-grained lineage. For example, ``most_frequent_words()`` operates on a single column and the ``top_25_words_plot`` is its own function. 
      - Favors chunking dataflow into meaningful assets to reduce the orchestration and I/O overhead per operation. Finer lineage is complex to achieve and requires using ``@op``, ``@graph``, ``@job``, and ``@asset`` (`ref <https://docs.dagster.io/guides/dagster/how-assets-relate-to-ops-and-graphs>`_)
    * - Documentation
      - Uses the native Python docstrings. Further metadata can be added using the ``@tag`` decorator. 
      - Uses ``MaterializeResult`` to store metadata.

----------------------
Dataflow execution
----------------------

.. table:: HackerNews top stories
   :align: left

   +-------------------------------------------------------------+------------------------------------------------------------+
   | Apache Hamilton                                             | Dagster                                                    |
   +=============================================================+============================================================+
   | .. literalinclude:: _dagster_snippets/hamilton_execution.py | .. literalinclude:: _dagster_snippets/dagster_execution.py | 
   |                                                             |                                                            |
   +-------------------------------------------------------------+------------------------------------------------------------+

.. list-table:: Key points
    :widths: 24 39 39
    :header-rows: 1

    * - Trait
      - Apache Hamilton
      - Dagster
    * - Execution instructions
      - Define a ``Driver`` using the ``Builder`` object. It automatically assembles the graph from the dataflow definition found in ``dataflow.py``
      - Load assets from Python modules using ``load_assets_from_modules`` then create an asset job by selecting assets to include. Finally, create a ``Definitions`` object to register on the orchestrator.
    * - Execution plane
      - ``Driver.materialize()`` executes the dataflow in a Python process. Can be called as a script, `using the CLI <https://blog.dagworks.io/p/a-command-line-tool-to-improve-your>`_, or programmatically.  
      - The `asset job is executed by the orchestrator <https://docs.dagster.io/concepts/assets/asset-jobs>`_, either through Dagster UI, by a scheduler/sensor/trigger, or via the CLI.
    * - Data I/O
      - I/O is decoupled from dataflow definition. People responsible for deployment can manage data sources without refactoring the dataflow. (Data I/O can be coupled if wanted.)
      - Data I/O is coupled with data assets which simplifies the execution code at the code of reusability.
    * - Framework code
      - Leverages a maximum of standard Python mechanisms (imports, env variables, etc.).
      - Most constructs requires Dagster-specific code to leverage protobuf serialization.


----------------
More information
----------------

For a full side-by-side example of Dagster and Apache Hamilton, visit `this GitHub repository <https://github.com/apache/hamilton/tree/main/examples/dagster>`_

For more questions, join our `Slack Channel <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_!
    