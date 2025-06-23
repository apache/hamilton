# Materialization

Apache Hamilton's driver allows for ad-hoc materialization. This enables you to take a DAG you already have,
and save your data to a set of custom locations/url.

Note that these materializers are _isomorphic_ in nature to the
[@save_to](https://hamilton.apache.org/reference/decorators/save_to/)
decorator. Materializers inject the additional node at runtime, modifying the
DAG to include a data saver node, and returning the metadata around materialization.

This framework is meant to be highly pluggable. While the set of available data savers is currently
limited, we expect folks to build their own materializers (and, hopefully, contribute them back to the community!).


## example
In this example we take the scikit-learn iris_loader pipeline, and materialize outputs to specific
locations through a driver call. We demonstrate:

1. Saving model parameters to a json file (using the default json materializer)
2. Writing a custom data adapters for:
   1. Pickling a model to an object file
   2. Saving confusion matrices to a csv file

See [run.py](run.py) for the full example.

In this example we only pass literal values to the materializers. That said, you can use both `source` (to specify the source from an upstream node),
and `value` (which is the default) to specify literals.


## `driver.materialize`

This will be a high-level overview. For more details,
see [documentation](https://hamilton.apache.org/reference/drivers/Driver/#hamilton.driver.Driver.materializehttps://hamilton.apache.org/reference/drivers/Driver/#hamilton.driver.Driver.materialize).

`driver.materialize()` does the following:
1. Processes a list of materializers to create a new DAG
2. Alters the output to include the materializer nodes
3. Processes a list of "additional variables" (for debugging) to return intermediary data
4. Executes the DAG, including the materializers
5. Returns a tuple of (`materialization metadata`, `additional variables`)

Materializers each consume:
1. A `dependencies` list to materialize
2. A (optional) `combine` parameter to combine the outputs of the dependencies
(this is required if there are multiple dependencies). This is a [ResultMixin](https://hamilton.apache.org/concepts/customizing-execution/#result-builders) object
3. an `id` parameter to identify the materializer, which serves as the nde name in the DAG

Materializers are referenced by the `to` object in `hamilton.io.materialization`, which utilizes
dynamic dispatch to create the appropriate materializer.

These refer to a `DataSaver`, which are keyed by a string (E.G `csv`).
Multiple data adapters can share the same key, each of which applies to a specific type
(E.G. pandas dataframe, numpy matrix, polars dataframe). New
data adapters are registered by calling `hamilton.registry.register_adapter`

## Custom Materializers

To define a custom materializer, all you have to do is implement the `DataSaver` class
(which will allow use in `save_to` as well.) This is demonstrated in [custom_materializers.py](custom_materializers.py).

## `driver.materialize` vs `@save_to`

`driver.materialize` is an ad-hoc form of `save_to`. You want to use this when you're developing, and
want to do ad-hoc materialization. When you have a production ETL, you can choose between `save_to` and `materialize`.
If the save location/structure is unlikely to change, then you might consider using `save_to`. Otherwise, `materialize`
is an idiomatic way of conducting the maerialization operations that cleanly separates side-effects from transformations.
