=======================
with_columns
=======================

We support the `with_columns` operation that appends the results as new columns to the original dataframe for several libraries:

Pandas
-----------------------

**Reference Documentation**

.. autoclass:: hamilton.plugins.h_pandas.with_columns
   :special-members: __init__


Polar (Eager)
-----------------------

**Reference Documentation**

.. autoclass:: hamilton.plugins.h_polars.with_columns
   :special-members: __init__


Polars (Lazy)
-----------------------

**Reference Documentation**

.. autoclass:: hamilton.plugins.h_polars_lazyframe.with_columns
   :special-members: __init__


PySpark
--------------

This is part of the hamilton pyspark integration. To install, run:

`pip install sf-hamilton[pyspark]`

**Reference Documentation**

.. autoclass:: hamilton.plugins.h_spark.with_columns
   :special-members: __init__
