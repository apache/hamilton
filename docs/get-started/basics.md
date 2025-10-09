# Apache Hamilton Basics

There are two parts to Apache Hamilton:

1. Apache Hamilton Functions.

   Apache Hamilton Functions are what you, the end user write.

2. Apache Hamilton Driver.

   Once you've written your functions, you will need to use the Apache Hamilton Driver to build the DAG and orchestrate
   execution.

Let's dive deeper into these parts below, but first a word on terminology.

We use the following terms interchangeably, e.g. a ____ in Apache Hamilton is ... :

* column
* variable
* node
* function

That's because we're representing columns as functions, which are parts of a directed acyclic graph. That is
 a column is a part of a dataframe. To compute a column we write a function that has input variables. From these functions
we create a DAG and represent each function as a node, linking each input variable by an edge to its respective node.

## Apache Hamilton Functions
Using Apache Hamilton is all about writing functions. From these functions a dataframe is constructed for you at execution time.

A simple (but rather contrived) example of what Apache Hamilton does that adds two numbers is as follows:

```python
def _sum(*vars):
    """Helper function to sum numbers.
    This is here to demonstrate that functions starting with _ do not get processed by hamilton.
    """
    return sum(vars)

def sum_a_b(a: int, b: int) -> int:
    """Adds a and b together
    :param a: The first number to add
    :param b: The second number to add
    :return: The sum of a and b
    """
    return _sum(a,b) # Delegates to a helper function
```

While this looks like a simple python function, there are a few components to note:
1. The function name `sum_a_b` is a globally unique key. In the DAG there can only be one function named `sum_a_b`.
   While this is not optimal for functionality reuse, it makes it extremely easy to learn exactly how a node in the DAG is generated,
   and separate out that logic for debugging/iterating.
2. The function `sum_a_b` depends on two upstream nodes -- `a` and `b`. This means that these values must either be:
    * Defined by another function
    * Passed in by the user as a configuration variable (see `Apache Hamilton Driver Code` below)
3. The function `sum_a_b` makes full use of the python type-hint system. This is required in Apache Hamilton,
   as it allows us to type-check the inputs and outputs to match with upstream producers and downstream consumers. In this case,
   we know that the input `a` has to be an integer, the input `b` has to also be an integer, and anything that declares `sum_a_b` as an input
   has to declare it as an integer.
4. Standard python documentation is a first-class citizen. As we have a 1:1 relationship between python functions and
   nodes, each function documentation also describes a piece of business logic.
5. Functions that start with _ are ignored, and not included in the DAG. Apache Hamilton tries to make use of every function
   in a module, so this allows us to easily indicate helper functions that won't become part of the DAG.


### Python Types & Apache Hamilton

Apache Hamilton makes use of python's type-hinting feature to check compatibility between function outputs and function inputs. However,
this is not particularly sophisticated, largely due to the lack of available tooling in python. Thus, generic types do not function correctly.
The following will not work:

```python
def some_func() -> Dict[str, int]:
    return {1: 2}
```

The following will both work:
```python
def some_func() -> Dict:
    return {1: 2}
```

```python
def some_func() -> dict:
    return {1: 2}
```

While this is unfortunate, the typing API in python is not yet sophisticated enough to rely on accurate subclass validation.

## Apache Hamilton Driver Code
For documentation on the actual Apache Hamilton Driver code, we invite the reader to [read the Driver class source code](/hamilton/driver.py) directly.

At a high level, the driver code does two things:

1. Create a Directed Acyclic Graph (DAG) from functions you define.
   ```python
   from hamilton import driver
   dr = driver.Driver(config, *modules_to_load)  # this creates the DAG from the modules you pass in.
   ```
2. It orchestrates execution given expected output and provided input.
   ```python
   df = dr.execute(final_vars, overrides, display_graph)  # this executes the DAG appropriately to create the dataframe.
   ```

The driver object also has a few other methods, e.g. `display_all_functions()`, `list_available_variables()`, but they're
really only used for debugging purposes.

Let's dive into the driver constructor call, and the execute method.

### Constructor Call to Driver()
The constructor call is pretty simple. Each constructor call sets up a DAG for execution given some configuration.
So if you want to change something about the DAG, very likely you'll need to create a new Driver() object.

#### config: Dict[str, Any], e.g. Configuration
The configuration is used not just to feed data to the DAG, but also to determine the structure of the DAG.
As such, it is passed in to the constructor, and used during DAG creation. This enables such decorators like @config.when.

Otherwise the contents of the _config_ dictionary should include all the inputs required for whatever final output you
want to create. The configuration dictionary should not be used for overriding what Apache Hamilton will compute.
To do this, use the `override` parameter as part of the `execute()` -- see below.

#### \*modules: ModuleType
This can be any number of modules. We traverse the modules in the order they are provided.

### Driver.execute()
The execute function determines the DAG walk required to get the requisite final variables (aka columns) that you want
in the dataframe. It also ensures that you have provided everything to execute properly.

Once it executes it uses a dictionary to memoize results, so that everything is only computed once. It executes the DAG
via a recursive depth-first-traversal, which leads to the possibility (although highly unlikely) of hitting python
recursion depth errors. If that happens, the culprit is almost always a circular reference in the graph. We suggest
displaying the DAG to verify this.

To help speed up development of new or existing Apache Hamilton Functions, we enable you to _override_ parts of the DAG. What
this means is that before calling `execute()`, you have computed some result that you want to use instead of what Apache Hamilton
would produce. To do so, you just pass in a dictionary of `{'col_name': YOUR_VALUE}` as the overrides argument to the
execute function.

To visualize the DAG that would be executed, pass the flag `display_graph=True` to execute. It will render an image in a pdf format.

# Backstory
For the backstory on Apache Hamilton we invite you to watch ~9 minute lightning talk on it that we gave at the apply conference:
[video](https://www.youtube.com/watch?v=B5Zp_30Knoo), [slides](https://www.slideshare.net/StefanKrawczyk/hamilton-a-micro-framework-for-creating-dataframes).
