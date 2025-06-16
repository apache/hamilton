=======================
parameterize_values
=======================
Expands a single function into n, each of which corresponds to a function in which the parameter value is replaced by
that `specific value`.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import parameterize_values
    import internal_package_with_logic

    ONE_OFF_DATES = {
         #output name        # doc string               # input value to function
        ('D_ELECTION_2016', 'US Election 2016 Dummy'): '2016-11-12',
        ('SOME_OUTPUT_NAME', 'Doc string for this thing'): 'value to pass to function',
    }
                # parameter matches the name of the argument in the function below
    @parameterize_values(parameter='one_off_date', assigned_output=ONE_OFF_DATES)
    def create_one_off_dates(date_index: pd.Series, one_off_date: str) -> pd.Series:
        """Given a date index, produces a series where a 1 is placed at the date index that would contain that event."""
        one_off_dates = internal_package_with_logic.get_business_week(one_off_date)
        return internal_package_with_logic.bool_to_int(date_index.isin([one_off_dates]))

We see here that ``parameterize`` allows you keep your code DRY by reusing the same function to create multiple
distinct outputs. The `parameter` key word argument has to match one of the arguments in the function. The rest of the
arguments are pulled from outside the DAG. The _assigned\_output_ key word argument takes in a dictionary of
tuple(Output Name, Documentation string) -> value.

----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.parameterize_values
   :special-members: __init__

Note: this was previously called `@parametrized`.
