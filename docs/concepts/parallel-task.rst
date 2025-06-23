Dynamic DAGs/Parallel Execution
----------------------------------

There are two approaches to parallel execution in Apache Hamilton:

1. Using an adapter that submits each node/function to a system that handles execution, e.g. ray, dask, async, or a threadpool.
2. Using the `Parallelizable[]` and `Collect[]` types + delegating to an executor.

Using an Adapter
================
The adapter approach effectively farms out the execution of each node/function to a system that can handle resolving
futures. That is, Apache Hamilton walks the DAG and submits each node to the adapter, which then submits the node for execution,
and internally the execution resolves any Futures from prior submitted nodes.

To make use of this, the general pattern is you apply an adapter to the driver and don't need to touch your Hamilton functions!:

.. code-block:: python

    from hamilton import driver
    from hamilton.execution import executors
    from hamilton.plugins.h_threadpool import FutureAdapter
    # from hamilton.plugins.h_ray import RayGraphAdapter
    # from hamilton.plugins.h_dask import DaskGraphAdapter

    dr = (
        driver.Builder()
        .with_modules(foo_module)
        .with_adapter(FutureAdapter())
        .build()
    )

    dr.execute(["my_variable"], inputs={...}, overrides={...})

The code above will execute the DAG submitting to a `ThreadPoolExecutor` (see :doc:`../reference/graph-adapters/ThreadPoolFutureAdapter`),
which is great if you're doing a lot of I/O bound work, e.g. making API calls, reading from a database, etc.

See this `Threadpool based example <https://github.com/apache/hamilton/blob/main/examples/parallelism/lazy_threadpool_execution/>`_ for a complete example.

Other adapters, e.g. Ray :doc:`../reference/graph-adapters/RayGraphAdapter`, Dask :doc:`../reference/graph-adapters/DaskGraphAdapter`, etc... will submit to their respective executors, but will involve object serialization
(see caveats below).

Using the `Parallelizable[]` and `Collect[]` types
==================================================


Apache Hamilton now has pluggable execution, which allows for the following:

1. Grouping of nodes into "tasks" (discrete execution unit between serialization boundaries)
2. Executing the tasks in parallel, using any executor of your choice

You can run this executor using the `Builder`, a utility class that allows you to build a driver piece by piece.
Note that you currently have to call `enable_dynamic_execution(allow_experimental_mode=True)`
which will toggle it to use the `V2` executor. Then, you can:

1. Add task executors to specify how to run the tasks
2. Add node grouping strategies
3. Add modules to crawl for functions
4. Add a results builder to shape the results

Either constructing the driver, or using the builder and `not` calling `enable_dynamic_execution` will give you the standard executor.
We highly recommend you use the builder pattern -- while the constructor of the `Driver` will be fully
backwards compatible according to the rules of semantic versioning, we may change it in the future (for 2.0).

Note that the new executor is required to handle dynamic creation of nodes (E.G. using `Parallelizable[]` and `Collect[]`.

Let's look at an example of the driver:

.. code-block:: python

    from my_code import foo_module, bar_module

    from hamilton import driver
    from hamilton.execution import executors

    dr = (
        driver.Builder()
        .with_modules(foo_module)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_config({"config_key": "config_value"})
        .with_local_executor(executors.SynchronousLocalTaskExecutor())
        .with_remote_executor(executors.MultiProcessingExecutor(max_tasks=5))
        .build()
    )

    dr.execute(["my_variable"], inputs={...}, overrides={...})

Note that we set a `remote` executor, and a local executor. While you can bypass this and instead set an `execution_manager`
in the builder call (see :doc:`../reference/drivers/Driver` for documentation on the `Builder`),this goes along with the default grouping strategy,
which is to place each node in its own group, except for
dynamically generated (`Parallelizable[]`) blocks, which are each made into one group, and executed locally.

Thus, when you write a DAG like this (a simple map-reduce pattern):

.. code-block:: python

    from hamilton.htypes import Parallelizable, Collect

    def url() -> Parallelizable[str]:
        for url_ in  _list_all_urls():
            yield url_

    def url_loaded(url: str) -> str:
        return _load(urls)

    def counts(url_loaded: str) -> int:
        return len(url_loaded.split(" "))

    def total_words(counts: Collect[int]) -> int:
        return sum(counts)

The block containing `counts` and `url_loaded` will get marked as one task, repeated for each URL in url_loaded,
and run on the remote executor (which in this case is the `ThreadPoolExecutor`).

Note that we currently have the following caveats:

1. No nested `Parallelizable[]`/`Collect[]` blocks -- we only allow one level of parallelization
2. Serialization for `Multiprocessing` is suboptimal -- we currently use the default `pickle` serializer, which breaks with certain cases. Ray, Dask, etc... all work well, and we plan to add support for joblib + cloudpickle serialization.
3. `Collect[]` input types are limited to one per function -- this is another caveat that we intend to get rid of, but for now you'll want to concat/put into one function before collecting.

Known Caveats
=============
If you're familiar with multi-processing then these caveats will be familiar to you. If not, then you should be aware of the following:

Serialization
^^^^^^^^^^^^^

Challenge:

* Objects are by default pickled and sent to the remote executor, and then unpickled.
* This can be slow, and can break with certain types of objects, e.g. OpenAI Client, DB Client, etc.

Solution:

* Make sure that your objects are serializable.
* If you're using a library that doesn't support serialization, then one option is to have Apache Hamilton instantiate
  the object in each parallel block. You can do this by making the code depend on something within the parallel block.
* Another option is write a customer wrapper function that uses `__set_state__` and `__get_state__` to serialize and deserialize the object.
* See `this issue <https://github.com/apache/hamilton/issues/743>`_ for details and possible features to make
  this simpler to deal with.


Multiple Collects
^^^^^^^^^^^^^^^^^

Currently, by design (see all limitations `here <https://github.com/apache/hamilton/issues/301>`_), you can only have one "collect" downstream of "parallel".

So the following code WILL NOT WORK:

.. code-block:: python

    import logging

    from hamilton import driver
    from hamilton.execution.executors import SynchronousLocalTaskExecutor
    from hamilton.htypes import Collect, Parallelizable
    import pandas as pd


    ANALYSIS_OB = tuple[tuple[str,...], pd.DataFrame]
    ANALYSIS_RES = dict[str, str | float]


    def split_by_cols(full_data: pd.DataFrame, columns: list[str]) -> Parallelizable[ANALYSIS_OB]:
        for idx, grp in full_data.groupby(columns):
            yield (idx, grp)


    def sub_metric_1(split_by_cols: ANALYSIS_OB, number: float=1.0) -> ANALYSIS_RES:
        idx, grp = split_by_cols
        return {"key": idx, "mean": grp["spend"].mean() + number}


    def sub_metric_2(split_by_cols: ANALYSIS_OB) -> ANALYSIS_RES:
        idx, grp = split_by_cols
        return {"key": idx, "mean": grp["signups"].mean()}


    def metric_1(sub_metric_1: Collect[ANALYSIS_RES], columns: list[str]) -> pd.DataFrame:
        data = [[k for k in d["key"]] + [d["mean"], "spend"] for d in sub_metric_1]
        cols = list(columns) + ["mean", "metric"]
        return pd.DataFrame(data, columns=cols)


    def metric_2(sub_metric_2: Collect[ANALYSIS_RES], columns: list[str]) -> pd.DataFrame:
        data = [[k for k in d["key"]] + [d["mean"], "signups"] for d in sub_metric_2]
        cols = list(columns) + ["mean", "metric"]
        return pd.DataFrame(data, columns=cols)


    # this will not work because you can't have two Collect[] calls downstream from a Parallelizable[] call
    def all_agg(metric_1: pd.DataFrame, metric_2: pd.DataFrame) -> pd.DataFrame:
        return pd.concat([metric_1, metric_2])


    if __name__ == "__main__":
        from hamilton.execution import executors
        import __main__

        from hamilton.log_setup import setup_logging
        setup_logging(log_level=logging.DEBUG)

        local_executor = executors.SynchronousLocalTaskExecutor()

        dr = (
            driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(__main__)
            .with_remote_executor(local_executor)
            .build()
        )
        df = pd.DataFrame(
            index=pd.date_range('20230101', '20230110'),
            data={
                "signups": [1, 10, 50, 100, 200, 400, 700, 800, 1000, 1300],
                "spend": [10, 10, 20, 40, 40, 50, 100, 80, 90, 120],
                "region": ["A", "B", "C", "A", "B", "C", "A", "B", "C", "X"],
            }
        )
        ans = dr.execute(
            ["all_agg"],
            inputs={
                "full_data": df,
                "number": 3.1,
                "columns": ["region"],
            }
        )
        print(ans["all_agg"])


To fix this, (this is documented in this `issue <https://github.com/apache/hamilton/issues/742>`_) you can either create a new function that combines the two `Collect[]` calls that could be combined with
:doc:`@config.when <../reference/decorators/config_when>`.

.. code-block:: python

    def all_metrics(sub_metric_1: ANALYSIS_RES, sub_metric_2: ANALYSIS_RES) -> ANALYSIS_RES:
        return ... # join the two dicts in whatever way you want

    def all_agg(all_metrics: Collect[ANALYSIS_RES]) -> pd.DataFrame:
        return ... # join them all into a dataframe

Or you use :doc:`@resolve <../reference/decorators/resolve>`,
with :doc:`@group (scroll down a little) <../reference/decorators/parameterize>`,
:doc:`@inject <../reference/decorators/inject>`,
to set what should be determined to be collected at DAG construction time:

.. code-block:: python

    @resolve(
        when=ResolveAt.CONFIG_AVAILABLE,
        decorate_with= lambda metric_names:
          inject( # this will annotate the function with @inject
             # it will then inject a group of values corresponding to the sources wanted
             sub_metrics=group(*[source(x) for x in metric_names])
          ),
    )
    def all_metrics(sub_metrics: list[ANALYSIS_RES], columns: list[str]) -> pd.DataFrame:
        frames = []
        for a in sub_metrics:
            frames.append(_to_frame(a, columns))
        return pd.concat(frames)

    # then in your driver:
    from hamilton import settings
    _config = {settings.ENABLE_POWER_USER_MODE:True}
    _config["metric_names"] = ["sub_metric_1", "sub_metric_2"]

    # Then in the driver building pass in the configuration:
    .with_config(_config)
