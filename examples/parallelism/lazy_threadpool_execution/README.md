# Lazy threadpool execution

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/parallelism/lazy_threadpool_execution/notebook.ipynb)

This example is different from the other examples under /parallelism/ in that
it demonstrates how to use an adapter to put each
function into a threadpool that allows for lazy DAG evaluation and for parallelism
to be achieved. This is useful when you have a lot of
functions doing I/O bound tasks and you want to speed
up the execution of your program. E.g. doing lots of
HTTP requests, reading/writing to disk, LLM API calls, etc.

> Note: this adapter does not support DAGs with Parallelizable and Collect functions; create an issue if you need this feature.

![DAG](my_functions.png)

The above image shows the DAG that will be executed. You can see from the structure
that the DAG can be parallelized, i.e. the left most nodes can be executed in parallel.

When you execute `run.py`, you will output that shows:

1. The DAG running in parallel -- check the image against what is printed.
2. The DAG logging to the Apache Hamilton UI -- please adjust for you project.
3. The DAG running without the adapter -- this is to show the difference in execution time.
4. An async version of the DAG running in parallel -- this is to show that the performance of this approach is similar.

```bash
python run.py
```

To use this adapter:

```python
from hamilton import driver
from hamilton.plugins import h_threadpool

# import your hamilton functions
import my_functions

# Create the adapter
adapter = h_threadpool.FutureAdapter()

# Create a driver
dr = (
    driver.Builder()
    .with_modules(my_functions)
    .with_adapters(adapter)
    .build()
)
# execute
dr.execute(["s", "x", "a"]) # if the DAG can be parallelized it will be

```
