=======================
Data quality
=======================

Apache Hamilton comes with data quality included out of the box.
While you can read more about this in the :doc:`API reference <../reference/decorators/index/>`, we have a few examples to help get you started.

The following two examples showcase a similar workflow, one using the vanilla hamilton data quality decorator, and the other using the pandera integration.
The goal of this is to show how to use runtime data quality checks in a larger, more complex ETL.

1. `Data quality with hamilton <https://github.com/apache/hamilton/tree/main/examples/data_quality/simple>`_
2. `Data quality with pandera <https://github.com/apache/hamilton/tree/main/examples/data_quality/pandera>`_

Async validators
~~~~~~~~~~~~~~~~

For validation logic that requires async operations (e.g., async database queries or API calls), use ``AsyncDataValidator`` or ``AsyncBaseDefaultValidator`` from ``hamilton.data_quality.base``. These define ``async def validate()`` and work with ``AsyncDriver``. You can mix sync and async validators in a single ``@check_output_custom`` call.

See the :doc:`check_output reference <../reference/decorators/check_output>` and `data quality writeup <https://github.com/apache/hamilton/blob/main/writeups/data_quality.md>`_ for details and examples.
