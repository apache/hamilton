=======================
parameterize_sources
=======================
Expands a single function into `n`, each of which corresponds to a function in which the parameters specified are
mapped to the specified inputs. Note this decorator and ``@parameterize_values`` are quite similar, except that the
input here is another DAG node(s), i.e. column/input, rather than a specific scalar/static value.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import parameterize_sources

    @parameterize_sources(
        D_ELECTION_2016_shifted=dict(one_off_date='D_ELECTION_2016'),
        SOME_OUTPUT_NAME=dict(one_off_date='SOME_INPUT_NAME')
    )
    def date_shifter(one_off_date: pd.Series) -> pd.Series:
        """{one_off_date} shifted by 1 to create {output_name}"""
        return one_off_date.shift(1)

We see here that ``parameterize_sources`` allows you to keep your code DRY by reusing the same function to create
multiple distinct outputs. The key word arguments passed have to have the following structure:

.. code-block:: python

    OUTPUT_NAME = Mapping of function argument to input that should go into it.

So in the example, ``D_ELECTION_2016_shifted`` is an _output_ that will correspond to replacing ``one_off_date`` with
``D_ELECTION_2016``. Then similarly ``SOME_OUTPUT_NAME`` is an _output_ that will correspond to replacing
``one_off_date`` with ``SOME_INPUT_NAME``. The documentation for both uses the same function doc and will replace
values that are templatized with the input parameter names, and the reserved value ``output_name``.

To help visualize what the above is doing, it is equivalent to writing the following two function definitions:

.. code-block:: python

    def D_ELECTION_2016_shifted(D_ELECTION_2016: pd.Series) -> pd.Series:
        """D_ELECTION_2016 shifted by 1 to create D_ELECTION_2016_shifted"""
        return D_ELECTION_2016.shift(1)

    def SOME_OUTPUT_NAME(SOME_INPUT_NAME: pd.Series) -> pd.Series:
        """SOME_INPUT_NAME shifted by 1 to create SOME_OUTPUT_NAME"""
        return SOME_INPUT_NAME.shift(1)

`Note`: that the different input variables must all have compatible types with the original decorated input variable.


----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.parameterize_sources
   :special-members: __init__


Note: this was previously called `@parameterized\_inputs`.
