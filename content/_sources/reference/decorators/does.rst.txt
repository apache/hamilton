=======================
does
=======================

``@does`` is a decorator that essentially allows you to run a function over all the input parameters. So you can't pass
any old function to ``@does``, instead the function passed has to take any amount of inputs and process them all in the
same way.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import does
    import internal_package_with_logic

    def sum_series(**series: pd.Series) -> pd.Series:
        """This function takes any number of inputs and sums them all together."""
        ...

    @does(sum_series)
    def D_XMAS_GC_WEIGHTED_BY_DAY(D_XMAS_GC_WEIGHTED_BY_DAY_1: pd.Series,
                                  D_XMAS_GC_WEIGHTED_BY_DAY_2: pd.Series) -> pd.Series:
        """Adds D_XMAS_GC_WEIGHTED_BY_DAY_1 and D_XMAS_GC_WEIGHTED_BY_DAY_2"""
        pass

    @does(internal_package_with_logic.identity_function)
    def copy_of_x(x: pd.Series) -> pd.Series:
        """Just returns x"""
        pass

The example here is a function, that all that it does, is sum all the parameters together. So we can annotate it with
the ``@does`` decorator and pass it the ``sum_series`` function. The ``@does`` decorator is currently limited to just
allow functions that consist only of one argument, a generic \*\*kwargs.


----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.does
   :special-members: __init__
