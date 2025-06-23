==================
Loading data
==================

While we've been injecting data in from the driver in previous examples, Hamilton functions are fully capable of loading their own data.
In the following example, we'll show how to use Apache Hamilton to:

1. Load data from an external source (CSV file and duckdb database)
2. Alter the source of data depending on how the DAG is parameterized/created
3. Mock data for a test-setting (so you can quickly execute your DAG without having to wait for data to load)

See the full tutorial `here <https://github.com/apache/hamilton/tree/main/examples/data_loaders>`_.
