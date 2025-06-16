===========================
Your First Dataflow
===========================

Let's get started with a dataflow that computes statistics on a time-series of marketing spend.

We're jumping in head-first. If you want to start with an overview, skip ahead to
:doc:`../concepts/index`.

.. note::

    You can follow along in the `examples directory <https://github.com/apache/hamilton/tree/main/examples/hello\_world>`_
    of the `hamilton repo <https://github.com/apache/hamilton/>`_. We highly recommend forking the repo and playing
    around with the code to get comfortable.

Write transformation functions
------------------------------

Create a file ``my_functions.py`` and add the following two functions:

.. code-block:: python

    import pandas as pd

    def avg_3wk_spend(spend: pd.Series) -> pd.Series:
        """Rolling 3 week average spend."""
        return spend.rolling(3).mean()

    def acquisition_cost(avg_3wk_spend: pd.Series, signups: pd.Series) -> pd.Series:
        """The cost per signup in relation to a rolling average of spend."""
        return avg_3wk_spend / signups

An astute observer might ask the following questions:

#. **Why do the parameter names clash with the function names?** This is core to how hamilton works. It utilizes dependency injection to create a DAG of computation. Parameter names tell the framework where your function gets its data.
#. **OK, if the parameter names determine the source of the data, why have we not defined defined `spend` or `signups` as functions?** This is OK, as we will provide this data as an input when we actually want to materialize our functions. The DAG doesn't have to be complete when it is compiled.
#. **Why is there no main line to call these functions?** Good observation. In fact, we never will call them (directly)! This is one of the core principles of Apache Hamilton. You write individual transforms and the rest is handled by the framework. More on that next.
#. **The functions all output pandas series. What if I don't want to use series?** You don't have to! Apache Hamilton is not opinionated on the data type you use. The following are all perfectly valid as well (and we support dask/spark/ray/other distributed frameworks).

Let's add a few more functions to our ``my_functions.py`` file:

.. code-block:: python

    def spend_mean(spend: pd.Series) -> float:
        """Shows function creating a scalar. In this case it computes the mean of the entire column."""
        return spend.mean()

    def spend_zero_mean(spend: pd.Series, spend_mean: float) -> pd.Series:
        """Shows function that takes a scalar. In this case to zero mean spend."""
        return spend - spend_mean

    def spend_std_dev(spend: pd.Series) -> float:
        """Function that computes the standard deviation of the spend column."""
        return spend.std()

    def spend_zero_mean_unit_variance(spend_zero_mean: pd.Series, spend_std_dev: float) -> pd.Series:
        """Function showing one way to make spend have zero mean and unit variance."""
        return spend_zero_mean / spend_std_dev

Let's give these functions a spin!

Run your dataflow
-----------------

To actually run the dataflow, we'll need to write :doc:`a driver <../concepts/driver>`. Create a\
``my_script.py`` with the following contents:

.. code-block:: python

    import logging
    import sys

    import pandas as pd

    # We add this to speed up running things if you have a lot in your python environment.
    from hamilton import registry; registry.disable_autoload()
    from hamilton import driver, base
    import my_functions  # we import the module here!


    logger = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stdout)

    if __name__ == '__main__':
        # Instantiate a common spine for your pipeline
        index = pd.date_range("2022-01-01", periods=6, freq="w")
        initial_columns = {  # load from actuals or wherever -- this is our initial data we use as input.
            # Note: these do not have to be all series, they could be scalar inputs.
            'signups': pd.Series([1, 10, 50, 100, 200, 400], index=index),
            'spend': pd.Series([10, 10, 20, 40, 40, 50], index=index),
        }
        dr = (
          driver.Builder()
            .with_config({})  # we don't have any configuration or invariant data for this example.
            .with_modules(my_functions)  # we need to tell hamilton where to load function definitions from
            .with_adapters(base.PandasDataFrameResult())  # we want a pandas dataframe as output
            .build()
        )
        # we need to specify what we want in the final dataframe (these could be function pointers).
        output_columns = [
            'spend',
            'signups',
            'avg_3wk_spend',
            'acquisition_cost',
        ]
        # let's create the dataframe!
        df = dr.execute(output_columns, inputs=initial_columns)
        # `pip install sf-hamilton[visualization]` earlier you can also do
        # dr.visualize_execution(output_columns,'./my_dag.png', {})
        print(df)

Run the script with the following command:

``python my_script.py``

And you should see the following output:

.. code-block:: bash

                spend  signups  avg_3wk_spend  acquisition_cost
    2022-01-02     10        1            NaN            10.000
    2022-01-09     10       10            NaN             1.000
    2022-01-16     20       50      13.333333             0.400
    2022-01-23     40      100      23.333333             0.400
    2022-01-30     40      200      33.333333             0.200
    2022-02-06     50      400      43.333333             0.125

Not only is your spend to signup ratio decreasing exponentially (your product is going viral!), but you've also
successfully run your first Apache Hamilton Dataflow. Kudos!

See, wasn't that quick and easy?

Note: if you're ever like "why are things taking a while to execute?", then you might have too much
in your python environment and Apache Hamilton is auto-loading all the extensions. You can disable this by
setting the environment variable ``HAMILTON_AUTOLOAD_EXTENSIONS=0`` or programmatically via
``from hamilton import registry; registry.disable_autoload()`` - for more see :doc:`../how-tos/extensions-autoloading`.
