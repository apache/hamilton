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

The `list_available_variables <../../drivers/Driver/#hamilton.driver.Driver.list_available_variables>`_ method accepts in a tag query, enabling search over the tags for specific matches.

----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.tag
   :special-members: __init__

.. autoclass:: hamilton.function_modifiers.tag_outputs
   :special-members: __init__
