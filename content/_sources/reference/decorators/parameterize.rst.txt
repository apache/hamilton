=======================
parameterize
=======================

Expands a single function into n, each of which correspond to a function in which the parameter value is replaced either
by:

#. A specified value ``value()``
#. The value from a specified upstream node ``source()``.

Note if you're confused by the other `@paramterize_*` decorators, don't worry, they all delegate to this base decorator.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import parameterize
    from hamilton.function_modifiers import value, source


    @parameterize(
        D_ELECTION_2016_shifted=dict(n_off_date=source('D_ELECTION_2016'), shift_by=value(3)),
        SOME_OUTPUT_NAME=dict(n_off_date=source('SOME_INPUT_NAME'), shift_by=value(1)),
    )
    def date_shifter(n_off_date: pd.Series, shift_by: int = 1) -> pd.Series:
        """{one_off_date} shifted by shift_by to create {output_name}"""
        return n_off_date.shift(shift_by)

By choosing ``value()`` or ``source()``, you can determine the source of your dependency. Note that you can also pass
documentation. If you don't, it will use the parameterized docstring.

.. code-block:: python

    @parameterize(
        D_ELECTION_2016_shifted=(dict(n_off_date=source('D_ELECTION_2016'), shift_by=value(3)), "D_ELECTION_2016 shifted by 3"),
        SOME_OUTPUT_NAME=(dict(n_off_date=source('SOME_INPUT_NAME'), shift_by=value(1)),"SOME_INPUT_NAME shifted by 1")
    )
    def date_shifter(n_off_date: pd.Series, shift_by: int=1) -> pd.Series:
        """{one_off_date} shifted by shift_by to create {output_name}"""
        return n_off_date.shift(shift_by)


----

**Reference Documentation**

Classes to help with @parameterize (also can be used with :doc:`@inject <inject>`):

.. autoclass:: hamilton.function_modifiers.ParameterizedExtract

.. autoclass:: hamilton.function_modifiers.source

.. autoclass:: hamilton.function_modifiers.value

.. autoclass:: hamilton.function_modifiers.group


Parameterize documentation:

.. autoclass:: hamilton.function_modifiers.parameterize
   :special-members: __init__
