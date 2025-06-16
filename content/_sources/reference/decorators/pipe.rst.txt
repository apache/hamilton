=======================
pipe family
=======================

We have a family of decorators that represent a chained set of transformations. This specifically solves the "node redefinition"
problem, and is meant to represent a pipeline of chaining/redefinitions. This is similar (and can happily be
used in conjunction with) ``pipe`` in pandas. In Pyspark this is akin to the common operation of redefining a dataframe
with new columns.

For some examples have a look at: https://github.com/apache/hamilton/tree/main/examples/scikit-learn/species_distribution_modeling

While it is generally reasonable to contain constructs within a node's function,
you should consider the pipe family for any of the following reasons:

1.  You want the transformations to display as nodes in the DAG, with the possibility of storing or visualizing
the result.

2. You want to pull in functions from an external repository, and build the DAG a little more procedurally.

3. You want to use the same function multiple times, but with different parameters -- while ``@does`` / ``@parameterize`` can
do this, this presents an easier way to do this, especially in a chain.

--------------

**Reference Documentation**

pipe
-----------------------------------------------------------------------
**DeprecationWarning from 2.0.0: use pipe_input instead**

.. autoclass:: hamilton.function_modifiers.macros.pipe
   :special-members: __init__

pipe_input
----------------
.. autoclass:: hamilton.function_modifiers.macros.pipe_input
   :special-members: __init__

pipe_output
----------------
.. autoclass:: hamilton.function_modifiers.macros.pipe_output
   :special-members: __init__

mutate
----------------
.. autoclass:: hamilton.function_modifiers.macros.mutate
   :special-members: __init__
