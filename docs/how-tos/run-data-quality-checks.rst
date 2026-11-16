=======================
Data quality
=======================

Apache Hamilton comes with data quality included out of the box.
While you can read more about this in the :doc:`API reference <../reference/decorators/index/>`, we have a few examples to help get you started.

The following two examples showcase a similar workflow, one using the vanilla hamilton data quality decorator, and the other using the pandera integration.
The goal of this is to show how to use runtime data quality checks in a larger, more complex ETL.

1. `Data quality with hamilton <https://github.com/apache/hamilton/tree/main/examples/data_quality/simple>`_
2. `Data quality with pandera <https://github.com/apache/hamilton/tree/main/examples/data_quality/pandera>`_

Custom validators
~~~~~~~~~~~~~~~~~

The ``@check_output`` decorator ships with default validators that cover common checks (data type, range, allowed values, etc. -- see the :doc:`check_output reference <../reference/decorators/check_output>`). When you need a check they don't cover -- say, a business rule specific to your data -- you can write your own validator class and apply it with ``@check_output_custom``.

A validator subclasses ``hamilton.data_quality.base.DataValidator`` and implements four methods, plus a constructor that forwards ``importance`` to the base class:

.. code-block:: python

    # my_module.py
    import pandas as pd

    from hamilton.data_quality import base


    class AllPositiveValidator(base.DataValidator):
        """Validates that a pandas series contains no negative values."""

        def __init__(self, importance: str):
            super().__init__(importance=importance)

        @classmethod
        def applies_to(cls, datatype: type) -> bool:
            return issubclass(datatype, pd.Series)

        def description(self) -> str:
            return "Validates that the series contains no negative values."

        @classmethod
        def name(cls) -> str:
            return "all_positive_validator"

        def validate(self, dataset: pd.Series) -> base.ValidationResult:
            negative_count = int((dataset < 0).sum())
            passes = negative_count == 0
            if passes:
                message = "All values are non-negative."
            else:
                message = f"Found {negative_count} negative value(s)."
            return base.ValidationResult(
                passes=passes,
                message=message,
                diagnostics={"negative_count": negative_count, "series_length": len(dataset)},
            )

The pieces are:

* ``applies_to`` -- whether this validator can run on the output type of the decorated function.
* ``description`` -- a human-readable description of the check; it becomes the documentation of the validator's node in the DAG.
* ``name`` -- used to name the validator's node in the DAG (see below).
* ``validate`` -- the actual check. It receives the decorated function's output and returns a ``ValidationResult``, which carries whether the check passed, a message, and an optional free-form ``diagnostics`` dictionary.
* ``importance`` -- every validator is constructed with ``importance="warn"`` or ``importance="fail"``, which determines what happens when the check fails (see below).

To apply it, pass validator *instances* to ``@check_output_custom``. You can pass multiple validators to a single decorator; note that you cannot stack ``@check_output_custom`` decorators on one function.

.. code-block:: python

    # my_module.py (continued)
    from hamilton.function_modifiers import check_output_custom


    @check_output_custom(AllPositiveValidator(importance="warn"))
    def prices_with_tax(prices: pd.Series, tax_rate: float) -> pd.Series:
        return prices * (1 + tax_rate)

At runtime, each validator runs on the function's output:

* With ``importance="warn"``, a failed check logs a warning (via the standard Python ``logging`` module) and execution continues.
* With ``importance="fail"``, a failed check raises ``hamilton.data_quality.base.DataValidationError``. All validators on the function are evaluated first, so the error reports every failure at once.

Under the hood, the decorator splits the function into several nodes: ``prices_with_tax_raw`` (the original function), one node per validator (named ``{function_name}_{validator_name}``, e.g. ``prices_with_tax_all_positive_validator``), and a final ``prices_with_tax`` node that acts on the validation results and returns the original output. The validator nodes are tagged with ``hamilton.data_quality.contains_dq_results`` (and ``hamilton.data_quality.source_node`` naming the node they validate), so you can locate them programmatically -- or simply request them as outputs to inspect the ``ValidationResult``:

.. code-block:: python

    # run.py
    import logging
    import sys

    import pandas as pd

    from hamilton import driver

    import my_module

    logging.basicConfig(stream=sys.stdout)  # so "warn" importance warnings are visible

    dr = driver.Builder().with_modules(my_module).build()
    results = dr.execute(
        ["prices_with_tax", "prices_with_tax_all_positive_validator"],
        inputs={"prices": pd.Series([10.0, 20.0, -5.0]), "tax_rate": 0.1},
    )
    print(results["prices_with_tax_all_positive_validator"])
    # ValidationResult(passes=False, message='Found 1 negative value(s).', ...)

If pandas series validation like the above is your main use case, also consider the pandera integration shown in example 2 above -- ``@check_output(schema=...)`` lets you express many checks declaratively without writing a validator class.

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
