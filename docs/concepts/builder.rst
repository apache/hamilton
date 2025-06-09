#######
Builder
#######

The :doc:`driver` page covered the basics of building the Driver, visualizing the dataflow, and executing the dataflow. We learned how to create the dataflow by passing a Python module to ``Builder().with_modules()``.

On this page, how to configure your Driver with the ``driver.Builder()``. There will be mentions of advanced concepts, which are further explained on their respective page.

.. note::

    As your Builder code grows complex, defining it over multiple lines can improve readability. This is possible by using parentheses after the assignment ``=``

    .. code-block:: python

        dr = (
            driver.Builder()
            .with_modules(my_dataflow)
            .build()
        )

    The order of Builder statements doesn't matter as long as ``.build()`` is last.


with_modules()
--------------

This passes dataflow modules to the Driver. When passing multiple modules, the Driver assembles them into a single dataflow.

.. code-block:: python

    # my_dataflow.py
    def A() -> int:
        """Constant value 35"""
        return 35

    def B(A: int) -> float:
        """Divide A by 3"""
        return A / 3

.. code-block:: python

    # my_other_dataflow.py
    def C(A: int, B: float) -> float:
        """Square A and multiply by B"""
        return A**2 * B

.. code-block:: python

    # run.py
    from hamilton import driver
    import my_dataflow
    import my_other_dataflow

    dr = driver.Builder().with_modules(my_dataflow, my_other_dataflow).build()

.. image:: ../_static/abc_basic.png
    :align: center


It encourages organizing code into logical modules (e.g., feature processing, model training, model evaluation). ``features.py`` might depend on PySpark and ``model_training.py`` on XGBoost. By organizing modules by dependencies, it's easier to reuse the XGBoost model training module in a project that doesn't use PySpark and avoid version conflicts.

.. code-block:: python

    # run.py
    from hamilton import driver
    import features
    import model_training
    import model_evaluation

    dr = (
        driver.Builder()
        .with_modules(features, model_training, model_evaluation)
        .build()
    )

.. note::

    Your modules may have same named functions which will raise an error when using ``.build()`` since we cannot have two nodes with the same name. You can use the method ``.allow_module_overrides()`` and Apache Hamilton will choose the function from the later imported module.



    .. code-block:: python

        dr = (
            driver.Builder()
            .with_modules(module_A, module_B)
            .allow_module_overrides()
            .build()
        )

    If ``module_A`` and ``module_B`` both have the function ``foo()``, Apache Hamilton will use ``module_B.foo()`` when constructing the DAG. See https://github.com/apache/hamilton/tree/main/examples/module_overrides for more info.

with_config()
-------------

This is directly related to the ``@config`` function decorator (see :ref:`config-decorators`) and doesn't have any effect in its absence. By passing a dictionary to ``with_config()``, you configure which functions will be used to create the dataflow. You can't change the config after the Driver is created. Instead, you need to rebuild the Driver with the new config values.

.. code-block:: python

    # my_dataflow.py
    from hamilton.function_modifiers import config

    def A() -> int:
        """Constant value 35"""
        return 35

    @config.when_not(version="remote")
    def B__default(A: int) -> float:
        """Divide A by 3"""
        return A / 3

    @config.when(version="remote")
    def B__remote(A: int) -> float:
        """Divide A by 2"""
        return A / 2

.. code-block:: python

    # run.py
    from hamilton import driver
    import my_dataflow

    dr = (
        driver.Builder()
        .with_modules(my_dataflow)
        .with_config(dict(version="remote"))
        .build()
    )

    dr.display_all_functions("dag.png")


.. image:: ./_snippets/config_when.png
    :align: center


with_materializers()
____________________

Adds `DataSaver` and `DataLoader` nodes to your dataflow. This allows to visualize these nodes using ``Driver.display_all_functions()`` and be executed by name with ``Driver.execute()``. More details on the :doc:`materialization` documentation page.

.. code-block:: python

    # my_dataflow.py
    import pandas as pd
    from hamilton.function_modifiers import config

    def clean_df(raw_df: pd.DataFrame) -> pd.DataFrame:
        return ...

    def features_df(clean_df: pd.DataFrame) -> pd.DataFrame:
        return ...

.. code-block:: python

    # run.py
    from hamilton import driver
    from hamilton.io.materialization import from_, to
    import my_dataflow

    loader = from_.parquet(target="raw_df", path="/my/raw_file.parquet")
    saver = to.parquet(
        id="features__parquet",
        dependencies=["features_df"],
        path="/my/feature_file.parquet"
    )

    dr = (
        driver.Builder()
        .with_modules(my_dataflow)
        .with_materializers(loader, saver)
        .build()
    )
    dr.display_all_functions("dag.png")

    dr.execute(["features__parquet"])

.. image:: ./_snippets/materializers.png
    :align: center


with_cache()
--------------

This enables Apache Hamilton's caching feature, which allows to automatically store intermediary results and reuse them in subsequent executions to skip computations. Learn more in the :doc:`/concepts/caching` section.

.. code-block:: python

    from hamilton import driver
    import my_dataflow

    dr = (
        driver.Builder()
        .with_modules(my_dataflow)
        .with_cache()
        .build()
    )


with_adapters()
---------------

This allows to add multiple Lifecycle hooks  to the Driver. This is a very flexible abstraction to develop custom plugins to do logging, telemetry, alerts, and more. The following adds a hook to launch debugger when reaching the node ``"B"``:

.. code-block:: python

    # run.py
    from hamilton import driver, lifecycle
    import my_dataflow

    debug_hook = lifecycle.default.PDBDebugger(node_filter="B", during=True)
    dr = (
        driver.Builder()
        .with_modules(my_dataflow)
        .with_adapters(debug_hook)
        .build()
    )

Other hooks are available to output a progress bar in the terminal, do experiment tracking for your Apache Hamilton runs, cache results to disk, send logs to DataDog, and more!

enable_dynamic_execution()
--------------------------

This directly relates to the Builder ``with_local_executor()`` and ``with_remote_executor()`` and the ``Parallelizable/Collect`` functions (see :doc:`parallel-task`). For the Driver to be able to parse them, you need to set ``allow_experimental_mode=True`` like the following:

.. code-block:: python

    # run.py
    from hamilton import driver
    import my_dataflow  # <- this contains Parallelizable/Collect nodes

    dr = (
        driver.Builder()
        .enable_dynamic_execution(allow_experimental_mode=True)  # set True
        .with_modules(my_dataflow)
        .build()
    )

By enabling dynamic execution, reasonable defaults are used for local and remote executors. You also specify them explicitly as such:

.. code-block:: python

    # run.py
    from hamilton import driver
    from hamilton.execution import executors
    import my_dataflow

    dr = (
        driver.Builder()
        .with_modules(my_dataflow)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_local_executor(executors.SynchronousLocalTaskExecutor())
        .with_remote_executor(executors.MultiProcessingExecutor(max_tasks=5))
        .build()
    )
