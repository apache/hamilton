# Classic Apache Hamilton Hello World

In this example we show you how to create a simple hello world dataflow that
creates a polars dataframe as a result. It performs a series of transforms on the
input to create columns that appear in the output.

File organization:

* `my_functions.py` houses the logic that we want to compute.
Note (1) how the functions are named, and what input
parameters they require. That is how we create a DAG modeling the dataflow we want to happen.
* `my_script.py` houses how to get Apache Hamilton to create the DAG, specifying that we want a polars dataframe and
exercise it with some inputs.

To run things:
```bash
> python my_script.py
```

You can even run this example in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/polars/notebook.ipynb)



# Visualizing Execution
Here is the graph of execution - which should look the same as the pandas example:

![polars](polars.png)

# Caveat with Polars
There is one major caveat with Polars to be aware of: THERE IS NO INDEX IN POLARS LIKE THERE IS WITH PANDAS.

What this means is that when you tell Apache Hamilton to execute and return a polars dataframe if you are using the
[provided results builder](https://github.com/apache/hamilton/blob/sf-hamilton-1.14.1/hamilton/plugins/h_polars.py#L8), i.e. `hamilton.plugins.h_polars.PolarsResultsBuilder`, then you will have to
ensure the row order matches the order you expect for all the outputs you request. E.g. if you do a filter, or a sort,
or a join, or a groupby, you will have to ensure that when you ask Apache Hamilton to materialize an output that it's in the
order you expect.

If you have questions, or need help with this example,
join us on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g), and we'll try to help!

Otherwise if you have ideas on how to better make Apache Hamilton work with Polars, please open an issue or start a discussion!
