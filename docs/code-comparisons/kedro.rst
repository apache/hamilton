Kedro
=========

Both ``Kedro`` and ``Apache Hamilton`` are Python tools to help define directed acyclic graph (DAG) of data transformations. While there's overlap between the two in terms of features, we note two main differences:

- ``Kedro`` is imperative and focuses on tasks; ``Apache Hamilton`` is declarative and focuses on assets.
- ``Kedro`` is heavier and comes with a project structure, YAML configs, and dataset definition to manage; ``Apache Hamilton`` is lighter to adopt and you can progressively opt-in features that you find valuable.

On this page, we'll dive into these differences, compare features, and present
some code snippets from both tools. 

.. note::
    See this `GitHub repository <https://github.com/apache/hamilton/tree/main/examples/kedro>`_ to compare a full project using Kedro or Apache Hamilton.

Imperative vs. Declarative
---------------------------

There are 3 steps to build and run a dataflow (a DAG, a data pipeline, etc.)

1. Define transformation steps 
2. Assemble steps into a dataflow
3. Execute the dataflow to produce data artifacts (tables, ML models, etc.)

1. Define steps
~~~~~~~~~~~~~~~

Imperative (``Kedro``) vs. declarative (``Apache Hamilton``) leads to significant differences in **Step 2** and **Step 3** that will shape how you work with the tool. However, **Step 1** remains similar. In fact, both tools use the term **nodes** to refer to steps.

.. table::
   :align: left

   +---------------------------------------------------------+------------------------------------------------------------+
   | Kedro (imperative)                                      | Apache Hamilton (declarative)                              |
   +=========================================================+============================================================+
   | .. literalinclude:: _kedro_snippets/kedro_definition.py | .. literalinclude:: _kedro_snippets/hamilton_definition.py | 
   |                                                         |                                                            |
   +---------------------------------------------------------+------------------------------------------------------------+

The function implementations are exactly the same. Yet, notice that the function names and docstrings were edited slightly. Imperative approaches like ``Kedro`` typically refer to steps as *tasks*  and prefer verbs to describe "the action of the function". Meanwhile, declarative approaches such as ``Apache Hamilton`` describe steps as *assets* and use nouns to refer to "the value returned by the function". This might appear superficial, but it relates to the difference in **Step 2** and **Step 3**.

2. Assemble dataflow
~~~~~~~~~~~~~~~~~~~~

With ``Kedro``, you need to take your functions from **Step 1** and create ``node`` objects, specifying the node's name, inputs, and outputs. Then, you create a ``pipeline`` from a set of ``nodes`` and ``Kedro`` assembles the nodes into a DAG. Imperative approaches need to specify how tasks (Kedro nodes) relate to each other.

With ``Apache Hamilton``, you pass the module containing all functions from **Step 1** and let Apache Hamilton create the ``nodes`` and the ``dataflow``. This is possible because in declarative approaches like Apache Hamilton, each function defines a transform **and** its dependencies on other functions. Notice how in **Step 1**, ``model_input_table()`` has parameters ``shuttles_preprocessed`` and ``companies_preprocessed``, which refers to other functions in the module. This contains all the required information to build the DAG.


.. table::
   :align: left

   +---------------------------------------------------------+------------------------------------------------------------+
   | Kedro (imperative)                                      | Apache Hamilton (declarative)                              |
   +=========================================================+============================================================+
   | .. literalinclude:: _kedro_snippets/kedro_assemble.py   | .. literalinclude:: _kedro_snippets/hamilton_assemble.py   | 
   |                                                         |                                                            |
   +---------------------------------------------------------+------------------------------------------------------------+

**Benefits of adopting a declarative approach**

- Less errors since you skip manual node creation (i.e., strings **will** lead to typos).

- Handle complexity since assembling a dataflow remains the same for 10 or 1000 nodes.

- Maintainability improves since editing your functions (**Step 1**) modifies the structure of your DAG, removing the pipeline definition as a failure point.

- Readability improves because you can understand how functions relate to each other without jumping between files.

These benefits of ``Apache Hamilton`` encourage developers to write smaller functions that are easier to debug and maintain, leading to major code quality gains. On the opposite, the burden of ``node`` and ``pipeline`` creation as projects grow in size lead to users stuffing more and more logic in a single node, making it increasingly harder to maintain.

3. Execute dataflow
~~~~~~~~~~~~~~~~~~~~

The primary way to execute ``Kedro`` pipelines is to use the command line tool with ``kedro run --pipeline=my_pipeline``. Pipelines are typically designed for all nodes to be executed while reading data and writing results while going through nodes. It is closer to macro-orchestration frameworks like Airflow in spirit.

On the opposite, ``Apache Hamilton`` dataflows are primarily meant to be executed programmatically (i.e., via Python code) and return results in-memory. This makes it easy to use ``Apache Hamilton`` within a :doc:`FastAPI service <../integrations/fastapi>` service or to power an LLM application.

For comparable side-by-side code, we can dig into ``Kedro`` and use the ``SequentialRunner`` programmatically. To return pipeline results in-memory we would need to hack further with ``kedro.io.MemoryDataset``.

.. note::
    Apache Hamilton also has rich support for I/O operations (see **Feature comparison** below)

.. table::
   :align: left

   +---------------------------------------------------------+------------------------------------------------------------+
   | Kedro (imperative)                                      | Apache Hamilton (declarative)                              |
   +=========================================================+============================================================+
   | .. literalinclude:: _kedro_snippets/kedro_execution.py  | .. literalinclude:: _kedro_snippets/hamilton_execution.py  | 
   |                                                         |                                                            |
   +---------------------------------------------------------+------------------------------------------------------------+

An imperative pipeline like ``Kedro`` is a series of step, just like a recipe. The user can specify "from nodes" or "to nodes" to *slice* the pipeline and not have to execute it in full.

For declarative dataflows like ``Apache Hamilton`` you request assets / nodes by name and the tool will determine the required nodes to execute (here ``"model_input_table"``) avoiding wasteful compute.

The simple Python interface provided by ``Apache Hamilton`` allows you to potentially define and execute your dataflow from a single file, which is great to kickstart an analysis or project. Just use ``python dataflow.py`` to execute it! 

.. code-block:: python

  # dataflow.py
  import pandas as pd

  def _is_true(x: pd.Series) -> pd.Series:
      return x == "t"

  def preprocess_companies(companies: pd.DataFrame) -> pd.DataFrame:
      """Preprocesses the data for companies."""
      companies["iata_approved"] = _is_true(companies["iata_approved"])
      return companies

  def preprocess_shuttles(shuttles: pd.DataFrame) -> pd.DataFrame:
      """Preprocesses the data for shuttles."""
      shuttles["d_check_complete"] = _is_true(
          shuttles["d_check_complete"]
      )
      shuttles["moon_clearance_complete"] = _is_true(
          shuttles["moon_clearance_complete"]
      )
      return shuttles

  def create_model_input_table(
      shuttles: pd.DataFrame, companies: pd.DataFrame,
  ) -> pd.DataFrame:
      """Combines all data to create a model input table."""
      shuttles = shuttles.drop("id", axis=1)
      model_input_table = shuttles.merge(
          companies, left_on="company_id", right_on="id"
      )
      model_input_table = model_input_table.dropna()
      return model_input_table

  if __name__ == "__main__":
      from hamilton import driver
      import dataflow  # import itself as a module

      dr = driver.Builder().with_modules(dataflow).build()
      inputs=dict(
          companies=pd.read_parquet("path/to/companies.parquet"),
          shuttles=pd.read_parquet("path/to/shuttles.parquet"),
      )
      results = dr.execute(["model_input_table"], inputs=inputs)


Framework weight
----------------

After imperative vs. declarative, the next largest difference is the type of user experience they provide. ``Kedro`` is a more opiniated and heavier framework; ``Apache Hamilton`` is on the opposite end of the spectrum and tries to be the lightest library possible. This changes the learning curve, adoption, and how each tool will integrate with your stack.

Kedro
~~~~~
``Kedro`` is opiniated and provides clear guardrails on how to do things. To begin using it, you'll need to learn to:

- Define nodes and register pipelines
- Register datasets using the data catalog construct
- Pass parameters to data runs
- Configure environment variables and credentials
- Navigate the project structure

This provides guidance when building your first data pipeline, but it's also a lot to take in at once. As you'll see in the `project comparison on GitHub <https://github.com/apache/hamilton/tree/main/examples/kedro>`_, ``Kedro`` involves more files making it harder to navigate. Also, it's reliant on YAML which is `generally seen as an unreliable format <https://noyaml.com/>`_. If you have an existing data stack or favorite library, it might clash with ``Kedro``'s way of thing (e.g., you have credentials management tool; you prefer `Hydra <https://hydra.cc/>`_ for configs).

Apache Hamilton
w~~~~~~~~~~~~~~~

``Apache Hamilton`` attempts to get you started quickly. In fact, this page pretty much covered what you need to know:

- Define nodes and a dataflow using regular Python functions (no need to even import ``hamilton``!)
- Build a ``Driver`` with your dataflow module and call ``.execute()`` to get results

``Apache Hamilton`` allows you to start light and opt-in features as your project's requirements evolve (data validation, scaling compute, testing, etc.). Python is a powerful language with rich editor support and tooling hence why it advocates for "everything in Python" instead of external configs in YAML or JSON. For example, parameters, data assets, and configurations can very much live as dataclasses within a ``.py`` file. ``Apache Hamilton`` was built with an extensive plugin system. There are many extensions, some contributed by users, to adapt Apache Hamilton to your project, and it's easy for you to extend yourself for further customization.

In fact, ``Apache Hamilton`` is so lightweight, you could even run it inside ``Kedro``!

Feature comparison
------------------

.. list-table::
    :widths: 24 39 39
    :header-rows: 1

    * - Trait
      - Kedro
      - Apache Hamilton
    * - Focuses on
      - Tasks (imperative)
      - Assets (declarative)
    * - Code structure
      - Opiniated. Makes assumptions about pipeline creation & registration and configuration.
      - Unopiniated.
    * - In-memory execution
      - Execute using a `KedroSession <https://docs.kedro.org/en/stable/kedro_project_setup/session.html>`_, but returning values in-memory is hacky.
      - Default
    * - I/O execution
      - `Datasets and Data Catalog <https://docs.kedro.org/en/stable/data/data_catalog.html>`_
      - `Data Savers & Loaders <https://hamilton.apache.org/concepts/materialization/>`_
    * - Expressive DAG definition
      - ⛔
      - `Function modifiers <https://hamilton.apache.org/concepts/function-modifiers/>`_
    * - Column-level transformations
      - ⛔
      - ✅
    * - LLM applications
      - ⛔ Limited by in-memory execution and return values.
      - ✅ declarative API in-memory makes it easy (`RAG app <https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/retrieval_augmented_generation>`_).
    * - Static DAG visualizations
      - Need ``Kedro Viz`` installed to export static visualizations.
      - Visualize entire dataflow, execution path, query what's upstream, etc. directly in a notebook or output to a file (``.png``, ``.svg``, etc.). Single dependency is ``graphviz``.
    * - Interactive DAG viewer
      - `Kedro Viz <https://github.com/kedro-org/kedro-viz>`_
      - `Apache Hamilton UI <https://github.com/apache/hamilton/tree/main/ui>`_
    * - Data validation
      - `Community Pandera plugin <https://github.com/Galileo-Galilei/kedro-pandera/releases>`_
      - `Native and Pandera plugin <https://hamilton.apache.org/how-tos/run-data-quality-checks/>`_
    * - Executors
      - `Sequential, multiprocessing, multi-threading <https://docs.kedro.org/en/stable/nodes_and_pipelines/run_a_pipeline.html>`_
      - Sequential, async, multiprocessing, multi-threading
    * - Executor extension
      - `Spark integration <https://docs.kedro.org/en/stable/integrations/pyspark_integration.html>`_
      - `PySpark <https://blog.dagworks.io/p/expressing-pyspark-transformations>`_, Dask, Ray, Modal
    * - Dynamic branching
      - ⛔
      - `Parallelizable/Collect <https://hamilton.apache.org/concepts/parallel-task/>`_ for easy parallelization.
    * - Command line tool (CLI)
      - ✅
      - ✅
    * - Node and pipeline testing
      - ✅
      - ✅
    * - Jupyter notebook extensions
      - ✅
      - ✅


Both ``Kedro`` and ``Apache Hamilton`` provide applications to view dataflows/pipelines and interact with their results. Here, ``Kedro`` provides a lighter webserver and UI, while ``Apache Hamilton`` offers a production-ready containerized application.


.. list-table::
    :widths: 24 39 39
    :header-rows: 1

    * - Trait
      - Kedro Viz
      - Apache Hamilton UI
    * - Interactive dataflow viewer
      - ✅
      - ✅
    * - View code definition of nodes
      - ✅
      - ✅
    * - Code versioning
      - Git SHA (may be out of sync with actual code)
      - Node-level versioning at runtime
    * - Collapsible view
      - ✅
      - ✅
    * - Tag nodes
      - ✅
      - ✅ 
    * - Execution observability
      - ⛔
      - ✅
    * - Artifact lineage and versioning
      - ⛔
      - ✅    
    * - Column-level lineage
      - ⛔
      - ✅
    * - Compare run results
      - ✅
      - ✅
    * - Rich artifact view
      - Preview 5 dataframe rows. Metadata about artifact (column count, row count, size).
      - Automatic statistical profiling of various dataframe libraries. 


More information
----------------

For a full side-by-side example of Kedro and Apache Hamilton, visit `this GitHub repository <https://github.com/apache/hamilton/tree/main/examples/kedro>`_

For more questions, join our `Slack Channel <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_
