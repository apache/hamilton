Builder
--------------
Use this to instantiate a driver.

.. autoclass:: hamilton.driver.Builder
   :special-members: __init__
   :members:

Driver
--------------
Use this driver in a general python context. E.g. batch, jupyter notebook, etc.

.. autoclass:: hamilton.driver.Driver
   :special-members: __init__
   :members:

DefaultGraphExecutor
---------------------
This is the default graph executor. It can handle limited parallelism
through graph adapters, and conducts execution using a simple recursive depth first traversal.
Note this cannot handle parallelism with `Parallelizable[]`/`Collect[]`. Note that this is only
exposed through the `Builder` (and it comes default on `Driver` instantiation) --
it is here purely for documentation, and you should never need to instantiate it directly.

.. autoclass:: hamilton.driver.DefaultGraphExecutor
   :special-members: __init__
   :members:

TaskBasedGraphExecutor
-----------------------

This is a task based graph executor. It can handle parallelism with the `Parallelizable`/`Collect` constructs,
allowing it to spawn dynamic tasks and execute them as a group. Note that this is only
exposed through the `Builder` when called with `enable_dynamic_execution(allow_experimental_mode: bool)` --
it is here purely for documentation, and you should never need to instantiate it directly.

.. autoclass:: hamilton.driver.TaskBasedGraphExecutor
   :special-members: __init__
   :members:
