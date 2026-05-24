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

Disabling validators at runtime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validators are useful during development but may be unnecessary overhead in a trusted production pipeline. You can disable all ``@check_output`` and ``@check_output_custom`` validators at graph-construction time, so no extra nodes are ever created:

.. code-block:: python

    dr = (
        hamilton.driver.Builder()
        .with_modules(my_pipeline)
        .with_data_quality_disabled()
        .build()
    )

This is equivalent to passing ``{"hamilton.data_quality.disable_checks": True}`` via ``.with_config()``, which is useful when the flag is controlled dynamically (e.g., from an environment variable):

.. code-block:: python

    import os

    dr = (
        hamilton.driver.Builder()
        .with_modules(my_pipeline)
        .with_config({"hamilton.data_quality.disable_checks": os.getenv("DISABLE_DQ", "false") == "true"})
        .build()
    )

Because the flag is resolved at graph-construction time, disabled drivers carry zero runtime overhead from validation — no validator nodes are created at all.

A second use case is graph visualization. Each decorated function normally expands into several nodes (``{name}_raw``, one per validator, and the final ``{name}`` node), which can clutter a visualization when you want to communicate pipeline structure rather than validation wiring. Building a driver with ``with_data_quality_disabled()`` gives a clean visualization with only the business-logic nodes:

.. code-block:: python

    dr_viz = (
        hamilton.driver.Builder()
        .with_modules(my_pipeline)
        .with_data_quality_disabled()
        .build()
    )
    dr_viz.display_all_functions("pipeline.png")

Note that this requires a separate driver instance from the one used for execution if you still want validations to run.

See the :doc:`check_output reference <../reference/decorators/check_output>` and `data quality writeup <https://github.com/apache/hamilton/blob/main/writeups/data_quality.md>`_ for details and examples.
