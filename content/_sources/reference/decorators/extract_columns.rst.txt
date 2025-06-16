=======================
extract_columns
=======================
This works on a function that outputs a dataframe, that we want to extract the columns from and make them individually
available for consumption. So it expands a single function into `n functions`, each of which take in the output
dataframe and output a specific column as named in the ``extract_columns`` decorator.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import extract_columns

    @extract_columns('fiscal_date', 'fiscal_week_name', 'fiscal_month', 'fiscal_quarter', 'fiscal_year')
    def fiscal_columns(date_index: pd.Series, fiscal_dates: pd.DataFrame) -> pd.DataFrame:
        """Extracts the fiscal column data.
        We want to ensure that it has the same spine as date_index.
        :param fiscal_dates: the input dataframe to extract.
        :return:
        """
        df = pd.DataFrame({'date_index': date_index}, index=date_index.index)
        merged = df.join(fiscal_dates, how='inner')
        return merged

Note: if you have a list of columns to extract, then when you call ``@extract_columns`` you should call it with an
asterisk like this:

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import extract_columns

    @extract_columns(*my_list_of_column_names)
    def my_func(...) -> pd.DataFrame:
       """..."""


----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.extract_columns
   :special-members: __init__
