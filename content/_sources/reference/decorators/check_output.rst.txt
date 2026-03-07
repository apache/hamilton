=======================
check_output*
=======================
The ``@check_output`` decorator enables you to add simple data quality checks to your code.

For example:

.. code-block:: python

    import pandas as pd
    import numpy as np
    from hamilton.function_modifiers import check_output

    @check_output(
        data_type=np.int64,
        range=(0,100),
    )
    def some_int_data_between_0_and_100() -> pd.Series:
        pass

The check\_output validator takes in arguments that each correspond to one of the default validators. These arguments
tell it to add the default validator to the list. The above thus creates two validators, one that checks the datatype
of the series, and one that checks whether the data is in a certain range.

Note that you can also specify custom decorators using the ``@check_output_custom`` decorator.

For async validation (e.g., async database or API calls), use ``AsyncDataValidator`` or ``AsyncBaseDefaultValidator``
from ``hamilton.data_quality.base`` as your base class instead of the sync variants. These define
``async def validate()`` and work with ``AsyncDriver``. You can mix sync and async validators in a single
``@check_output_custom`` call — each gets the appropriate wrapper type automatically.

See `data_quality <https://github.com/apache/hamilton/blob/main/data\_quality.md>`_ for more information on
available validators and how to build custom ones.

Note we also have a plugins that allow for validation with the pandera and pydantic libraries. There are two ways to access these:

1. ``@check_output(schema=pandera_schema)`` or ``@check_output(model=pydantic_model)``
2. ``@h_pandera.check_output()`` or ``@h_pydantic.check_output()`` on the function that declares either a typed dataframe or a pydantic model.

----

**Reference Documentation**

.. autoclass:: hamilton.function_modifiers.check_output
   :special-members: __init__

.. autoclass:: hamilton.function_modifiers.check_output_custom
   :special-members: __init__

.. autoclass:: hamilton.data_quality.base.AsyncDataValidator
   :members: validate, applies_to, description, name

.. autoclass:: hamilton.data_quality.base.AsyncBaseDefaultValidator
   :members: validate, applies_to, description, arg, name

.. autoclass:: hamilton.plugins.h_pandera.check_output
   :special-members: __init__

.. autoclass:: hamilton.plugins.h_pydantic.check_output
   :special-members: __init__
