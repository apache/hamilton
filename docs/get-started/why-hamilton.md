# Why use Apache Hamilton?

There are many choices for building dataflows/pipelines/workflows/ETLs.
Let's compare Apache Hamilton to some of the other options to help answer this question.

## Comparison to Other Frameworks

There are a lot of frameworks out there, especially in the pipeline space. This section should help you figure out when to
use Apache Hamilton with another framework, or in place of a framework, or when to use another framework altogether.

Let's go over some groups of "competitive" or "complimentary" products. For a basic overview,
see the product matrix on the [homepage](../index.md).

### Orchestration Systems
Examples include:
- [Airflow](https://airflow.apache.org/)
- [Metaflow](https://github.com/Netflix/metaflow)
- [Luigi](https://github.com/spotify/luigi)
- [dbt](https://www.getdbt.com/)

Apache Hamilton is not, in itself a macro, i.e. high level, task orchestration system. While it does orchestrate functions,
and the DAG abstraction is very powerful, it does not provision compute,
or schedule long-running jobs. Apache Hamilton works well in conjunction with these macro systems.
Apache Hamilton provides the capabilities of fine-grained lineage, highly readable code, and self-documenting pipelines,
which many of these systems lack.

Apache Hamilton can be used within any python orchestration system in the following ways:

1. _Hamilton DAGs can be called within orchestration system tasks._
See the [Apache Hamilton + Airflow example](https://blog.dagworks.io/p/supercharge-your-airflow-dag-with). The integration is generally trivial -- all you have to do
is call out to the hamilton library within your task. If your orchestrator supports python, then you're good to go. Some pseudocode (if your orchestrator handles scripts like airflow):

    ```python
    #my_task.py
    import hamilton
    import my_transformations
    dr = hamilton.driver.Driver({}, my_functions)
    output = dr.execute(['final_var'], inputs=...)
    do_something_with(output)
    ```
2. _Hamilton DAGs can be broken up to run as components within an orchestration system._
With the ability to include [overrides](../concepts/driver.rst),
you can run the DAG on each task, overloading the outputs of the last task + any static inputs/configuration, and pass it into the next task. This is more
of a manual/power-user feature. Some pseudocode:

    ```python
    #my_task.py
    import hamilton
    import my_functions
    prior_inputs = load_relevant_task_results()
    desired_outputs = ['final_var_1', 'final_var_2']
    inputs = my_inputs
    dr = hamilton.driver.Driver({}, my_functions)
    output = dr.execute(
       desired_outputs,
       inputs=inputs,
       overrides=prior_inputs)
    save_for_later(output)
    ```

### Feature Stores

Examples include:
- [Hopsworks](https://www.hopsworks.ai/)
- [Feast](https://feast.dev/)
- [Tecton](https://tecton.ai/)

One can think of Apache Hamilton as a being your "feature definition store", where "store" is code + git. While it does
not provide all the capabilities of a standard feature store, it provides a source of truth for the code that
generated the features, and can be run in a portable method. *So*, if your desire is just to be able to run the same
code in different environments, and have an online/offline store of features, you can use hamilton both to save the
features offline, and generate features online on the fly.

See the [feature engineering example](../how-tos/use-for-feature-engineering.rst) for more possibilities, as
well as [blogs on the feature topic](https://blog.dagworks.io/?sort=search&search=features).

Note that in small cases, you probably don't need a true feature store -- recomputing derived features in an ETL
and online can be very efficient, as long as you have some database to look values up (or have them passed in).

Also note that joins and aggregations can get tricky. We often recommend using our "polymorphic function
definition" i.e. functions decorated with `@config.when`, to either load up the non-online-friendly features
from a feature store or do an external lookup to simulate an online join.

We expect Apache Hamilton to play a prominent role in the way feature stores work in the future.

### Data Science Ecosystems/ML platforms
Examples include:
- [Kedro](https://kedro.org/)
- [Domino Data Labs](https://www.dominodatalab.com/)
- [Dataiku](https://www.dataiku.com/)
- [SageMaker](https://aws.amazon.com/sagemaker/)
- [Google Cloud Vertex AI Platform](https://cloud.google.com/vertex-ai)
- etc.

We've kind of grouped a whole suite of platforms into the same bucket here. These
tend to have a lot of capabilities all related to ML. Apache Hamilton can be used in conjunction with these
platforms in a variety of ways. For example, you can use Apache Hamilton to generate features for a model
that you train in one of these platforms. Or you can use Apache Hamilton to generate a model using the
platform's compute, and then save the model to the platform's registry.

### Registries / Experiment Tracking
Examples include:
- [MLflow](https://mlflow.org/)
- [Weights and Biases](https://wandb.ai/site)
- [DVC](https://dvc.org/)

Most pipelines have a "reverse ETL problem" -- they need to get the results of the pipeline into a some
sort of datastore or registry. Apache Hamilton can be used in conjunction with these tools as the glue code
that helps everything work together. For example, you can use Apache Hamilton to generate a model
and then store metrics computed by Apache Hamilton to one of these "destinations".

There are three main ways to integrate with these tools:
 - inside a function that Apache Hamilton orchestrates
 - outside Apache Hamilton (e.g. in a script that calls Apache Hamilton)
 - using "materializers" (see [materializers](../reference/io/index.rst)) (see [this blog](https://blog.dagworks.io/p/separate-data-io-from-transformation)).

See this [ML reference post](https://blog.dagworks.io/p/from-dev-to-prod-a-ml-pipeline-reference) for examples of how to use Apache Hamilton with these tools.

### Python Dataframe/manipulation Libraries
Examples include:
- [pandas](https://pandas.pydata.org/)
- [dask](https://www.dask.org/)
- [modin](https://github.com/modin-project/modin)
- [polars](https://www.pola.rs/)
- [duckdb](https://duckdb.org/)

Apache Hamilton works with any python dataframe/manipulation oriented libraries.
See our [examples folder](https://github.com/apache/hamilton/tree/main/examples)
to see how to use Apache Hamilton with these libraries.


### Python "big data" systems
The following systems are ones that you would resort to using when wanting to scale up your data processing.

Examples include:
- [dask](https://www.dask.org/)
- [ray](https://ray.io/)
- [pyspark](https://spark.apache.org/docs/latest/api/python/)
- [pandas-on-spark](https://spark.apache.org/docs/latest/api/python/user_guide/pandas_on_spark/index.html)

These all provide capabilities to either (a) express and execute computation over datasets in python or (b)
parallelize it. Often both. Apache Hamilton has a variety of integrations with these systems. The basics is that Apache Hamilton
can make use of these systems to execute the DAG using the [GraphAdapter](../reference/graph-adapters/index.rst) abstraction and [Lifecycle Hooks](../reference/lifecycle-hooks/index.rst).

See our [examples folder](https://github.com/apache/hamilton/tree/main/examples)
to see how to use Apache Hamilton with these systems.
