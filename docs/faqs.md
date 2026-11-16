<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

# Frequently Asked Questions

This page collects common starting points for Apache Hamilton users. Each answer is intentionally brief; follow the links for the detailed concepts and examples.

## How do I cache a workflow and restart it later?

**TL;DR:** Enable caching with `Builder().with_cache()` so Hamilton stores node results and reuses unchanged work in later executions. Because cache keys include node code and dependency data versions, you can stop and restart a workflow or move investigation to another environment without recomputing compatible results.

Read next:

- [Caching concept](concepts/caching.rst)
- [Caching tutorial](how-tos/caching-tutorial.ipynb)
- [Caching reference](reference/caching/caching-logic.rst)

## How do I filter or join data with Series?

**TL;DR:** Keep filtering, joining, and other dataframe or Series operations inside ordinary typed Hamilton functions, using the API of the dataframe library you return and accept. For reusable feature transformations, model intermediate Series or columns as nodes and use `@extract_columns` when column-level lineage or reuse is useful.

Read next:

- [Feature engineering with Apache Hamilton](how-tos/use-for-feature-engineering.rst)
- [Function modifiers](concepts/function-modifiers.rst)
- [Ibis integration for table filters and joins](integrations/ibis/index.md)
- [Extract columns reference](reference/decorators/extract_columns.rst)

## How do I handle Spark DataFrames?

**TL;DR:** Treat a Spark DataFrame as the input or output of typed Hamilton functions and keep Spark transformations in those functions, just as you would with pandas or another dataframe library. For distributed execution, use the Spark examples and choose the Spark graph adapter or decorators that match whether you are composing Spark transformations or generating PySpark UDFs.

Read next:

- [Spark examples](https://github.com/apache/hamilton/tree/main/examples/spark)
- [Spark graph adapters](reference/graph-adapters/index.rst)
- [`with_columns` Spark reference](reference/decorators/with_columns.rst)
- [Scaling computation](how-tos/scale-up.rst)

## How can I scale up?

**TL;DR:** Separate transformation logic from execution, then scale the appropriate dimension: use Ray or Dask for parallelizing transformations, or Spark and pandas-on-Spark for larger distributed datasets. Start with the scaling guide and the corresponding integration example, then select the execution adapter that fits your workload and deployment environment.

Read next:

- [Scaling computation](how-tos/scale-up.rst)
- [Parallel task execution](concepts/parallel-task.rst)
- [Graph adapters reference](reference/graph-adapters/index.rst)
- [Integrations](integrations/index.rst)

## How do I configure my pipeline?

**TL;DR:** Build a `Driver` with `Builder()` and configure modules, runtime configuration, materializers, caching, lifecycle hooks, and execution adapters before calling `.build()`. Use `with_config()` with `@config` decorators when configuration should select which functions become nodes, and rebuild the Driver when those configuration values change.

Read next:

- [Builder configuration](concepts/builder.rst)
- [Driver concept](concepts/driver.rst)
- [Function modifiers](concepts/function-modifiers.rst)
- [Materialization](concepts/materialization.rst)
