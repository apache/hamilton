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
