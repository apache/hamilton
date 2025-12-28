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


# Scaling Apache Hamilton on Spark
## Pyspark

If you're using pyspark, Apache Hamilton allows for natural manipulation of pyspark dataframes,
with some special constructs for managing DAGs of UDFs.

See the examples in `pyspark` & `world_of_warcraft` and `tpc-h` to learn more.

## Pandas
If you're using Pandas, Apache Hamilton scales by using Koalas on Spark.
Koalas became part of Spark officially in Spark 3.2, and was renamed Pandas on Spark.
The example in `pandas_on_spark` here assumes that.

## Pyspark UDFs
If you're not using Pandas, then you can use Apache Hamilton to manage and organize your pyspark UDFs.
See the example in `pyspark_udfs`.

Note: we're looking to expand coverage and support for more Spark use cases. Please come find us, or open an issue,
if you have a use case that you'd like to see supported!

## Caveats

Apache Hamilton's type-checking doesn't inherently work with spark connect, which can swap out different types of dataframes that
are not part of the same subclass. Thus when you are passing in a spark session or spark dataframe as an input,
you can use the `SparkInputValidator` (available by instantiation or access of the static field `h_spark.SPARK_INPUT_CHECK`).

```python
from hamilton import driver
from hamilton.plugins import h_spark

dr = driver.Builder().with_modules(...).with_adapters(h_spark.SPARK_INPUT_CHECK).build()
```
