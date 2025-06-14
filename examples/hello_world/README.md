# Classic Apache Hamilton Hello World

In this example we show you how to create a simple hello world dataflow that
creates a dataframe as a result. It performs a series of transforms on the
input to create columns that appear in the output.

File organization:

* `my_functions.py` houses the logic that we want to compute. Note how the functions are named, and what input
parameters they require. That is how we create a DAG modeling the dataflow we want to happen.
* `my_script.py` houses how to get Apache Hamilton to create the DAG and exercise it with some inputs.
* `my_notebook.ipynb` houses how one might iterate in a notebook environment and provide a way to inline define Apache Hamilton
functions and add them to the DAG constructed. To be clear, it is not used by `my_script.py`, but showing an alternate path
to running/developing things.

To run things:
```bash
> python my_script.py
```

To exercise this example you can run it in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/hello_world/my_notebook.ipynb)


If you have questions, or need help with this example,
join us on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g), and we'll try to help!

# Visualizing Execution
Here is the graph of execution - pretty simple, right?

![my_dag](my_dag.dot.png)
