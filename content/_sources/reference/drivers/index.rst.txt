========
Drivers
========

Currently, we have one `main driver <https://github.com/apache/hamilton/blob/main/hamilton/driver.py>`__.
It's highly parameterizable, allowing you to customize:

* The way the DAG is executed (how each node is executed), i.e. either locally, in parallel, or on a cluster!
* How the results are materialized back to you -- e.g. a DataFrame, a dictionary, your custom object!

To tune the above, pass in a Graph Adapter, a Result Builder, and/or anotehr lifecycle method -- see :doc:`../result-builders/index`, :doc:`../graph-adapters/index`.

Let's walk through how you might use the Hamilton Driver.

Instantiation
=============

#. Determine the configuration required to setup the DAG.
#. Provide the python modules that should be crawled to create the DAG.
#. Optional. Determine the return type of the object you want ``execute()`` to return. Default is to create a Pandas DataFrame.

.. code-block:: python

    from hamilton import driver
    from hamilton import base

    # 1. Setup config. See the Parameterizing the DAG section for usage
    config = {}

    # 2. we need to tell hamilton where to load function definitions from
    module_name = 'my_functions'
    module = importlib.import_module(module_name)  # or simply "import my_functions"

    # 3. Determine the return type -- default is a pandas.DataFrame.
    adapter = base.SimplePythonDataFrameGraphAdapter() # See GraphAdapter docs for more details.

    # These all feed into creating the driver & thus DAG.
    dr = driver.Driver(config, module, adapter=adapter)


Execution
=========

Using a DAG once
****************

This approach assumes that all inputs were passed in with the ``config`` dictionary above.

.. code-block:: python

    output = ['output1', 'output2', ...]
    df = dr.execute(output)

Using a DAG multiple times
**************************

This approach assumes that at least one input is not provided in the ``config`` dictionary provided to the constructor,
and instead you provide that input to each ``execute`` invocation.

.. code-block:: python

    output = ['output1', 'output2', ...]
    for data in dataset:  # if data is a dict of values.
        df = dr.execute(output, inputs=data)

Short circuiting some DAG computation
*************************************

This will force Apache Hamilton to short circuit a particular computation path, and use the passed in override as a result of
that particular node.


.. code-block:: python

    output = ['output1', 'output2', ...]
    df = dr.execute(output, overrides={'intermediate_node': intermediate_value})


Reference
---------

.. toctree::
   :maxdepth: 2

   Driver
   AsyncDriver
   Custom
