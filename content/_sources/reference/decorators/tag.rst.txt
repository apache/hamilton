=======================
tag*
=======================

Allows you to attach metadata to a node (any node decorated with the function). A common use of this is to enable
marking nodes as part of some data product, or for GDPR/privacy purposes.

For instance:

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import tag

    def intermediate_column() -> pd.Series:
        pass

    @tag(data_product='final', pii='true')
    def final_column(intermediate_column: pd.Series) -> pd.Series:
        pass

**How do I query by tags?**

Right now, we don't have a specific interface to query by tags, however we do expose them via the driver. Using the
``list_available_variables()`` capability exposes tags along with their names & types, enabling querying of the
available outputs for specific tag matches. E.g.

.. code-block:: python

    from hamilton import driver
    dr = driver.Driver(...)  # create driver as required
    all_possible_outputs = dr.list_available_variables()
    desired_outputs = [o.name for o in all_possible_outputs
                       if 'my_tag_value' == o.tags.get('my_tag_key')]
    output = dr.execute(desired_outputs)


**Using display_name for visualization**

You can use the special ``display_name`` tag to provide a human-readable name for nodes in graphviz visualizations.
This allows you to show user-friendly names in DAG diagrams while keeping valid Python identifiers as function names.

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import tag

    @tag(display_name="Customer Lifetime Value")
    def customer_ltv(purchases: pd.DataFrame, tenure: pd.Series) -> pd.Series:
        """Calculate customer lifetime value."""
        return purchases.sum() * tenure

When you visualize the DAG using ``dr.display_all_functions()``, the node will display "Customer Lifetime Value"
instead of "customer_ltv". This is useful for:

- Creating presentation-ready diagrams for stakeholders
- Adding business-friendly names for technical functions
- Making visualizations more readable for non-technical audiences

Note that ``display_name`` only affects visualization - the actual node name used in code remains the function name.


----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.tag
   :special-members: __init__

.. autoclass:: hamilton.function_modifiers.tag_outputs
   :special-members: __init__
