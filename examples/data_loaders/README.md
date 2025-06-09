# Data Loaders

Among multiple uses, Apache Hamilton excels at building maintainable, scalable representations of ETLs.
If you've read through the other guides, it should be pretty clear how hamilton enables transformations (the T in ETL/ELT).
In this example, we'll talk about an approach to _Extracting_ data, and how Apache Hamilton enables you to build out extracts,
in a scalable, pluggable way. For example, being able to switch where data is loaded between development and production
is useful, since you might only want a subsample in development, or even load it from a different source.
Here we'll show you how you can achieve this without cluttering your code with `if else`,
which will make your dataflow easier to maintain in the long run.

The goal is to show you two things:

1. How to load data from various sources
2. How to switch the sources of data you're loading from by swapping out modules, using [polymorphism](https://en.wikipedia.org/wiki/Polymorphism_(computer_science))

As such, we have three data loaders to use:

1. [load_data_mock.py](load_data_mock.py): generates mock data on the fly. Meant to represent a unit-testing/quick iteration scenario.
2. [load_data_csv.py](load_data_csv.py): Uses CSV data. Meant to represent more ad-hoc research.
3. [load_data_duckdb.py](load_data_duckdb.py) Uses a duckdb database (saved locally). Meant to represent more production-ready dataflows,
as well as demonstrate the ease of working with duckdb.

But this is hardly exclusive, or exhaustive. One can easily imagine loading from snowflake, your custom datawarehouse, hdfs, etc...
All by swapping out the data loaders.

# The data

The data comes pregenerated in (test_data)[test_data], in both `.csv` and `.duckdb` format.

# Loading/Analyzing the data

To load/analyze the data, you can run the script `run.py`

- `python run.py csv` reads from the `.csv` files and runs all the variables
- `python run.py duckdb` reads from the `duckdb` database and runs all the variables
- `python run.py mock` creates mock data and runs the pipeline

Note that you, as the user, have to manually handle connections/whatnot for duckdb.
We are currently designing the ability to do this natively in hamilton: https://github.com/apache/hamilton/issues/197.

# Execution Graphs
You'll see that the execution graphs are practically the same, except for the top part. Which is exactly what we want,
because the data_loader modules defines the same set of functions, but have different requirements for getting the data!

## CSV
![csv](csv_execution_graph.png)
## DuckDB
![duckdb](duckdb_execution_graph.png)
## Mock
![mock](mock_execution_graph.png)
