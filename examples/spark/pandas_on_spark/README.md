# Apache Hamilton on Koalas Spark 3.2+

Here we have a hello world example showing how you can
take some Apache Hamilton functions and then easily run them
in a distributed setting via Spark 3.2+ using Koalas.

`pip install sf-hamilton[pyspark]`  or `pip install sf-hamilton pyspark[pandas_on_spark]` to for the right dependencies to run this example.

File organization:

* `business_logic.py` houses logic that should be invariant to how hamilton is executed.
* `data_loaders.py` houses logic to load data for the business_logic.py module. The
idea is that you'd swap this module out for other ways of loading data.
*  `run.py` is the script that ties everything together.

# DAG Visualization:
Here is the visualization of the execution when you'd execute `run.py`:

![pandas_on_spark.png](pandas_on_spark.png)
