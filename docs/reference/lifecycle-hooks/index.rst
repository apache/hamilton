==================
Lifecycle Adapters
==================

Currently a few of the API extensions are still experimental. Note this doesn't mean they're not well-tested or thought out -- rather that we're actively looking for feedback. More docs upcoming, but for now fish around the `experimental package <https://github.com/apache/hamilton/tree/main/hamilton/experimental>`_, and give the extensions a try!

The other extensions live within `plugins <https://github.com/apache/hamilton/tree/main/hamilton/plugins>`_. These are fully supported and will be backwards compatible across major versions.

Customization
-------------

The subsequent documents contain public-facing APIs for customizing Apache Hamilton's
execution. Note that the public-facing APIs are still a work in progress -- we
will be improving the documentation. We plan for the APIs, however, to be stable
looking forward.

.. toctree::
   ResultBuilder
   LegacyResultMixin
   GraphAdapter
   NodeExecutionHook
   GraphExecutionHook
   EdgeConnectionHook
   NodeExecutionMethod
   StaticValidator
   GraphConstructionHook
   TaskSubmissionHook
   TaskReturnHook
   TaskExecutionHook
   TaskGroupingHook

Available Adapters
-------------------

In addition to the base classes for lifecycle adapters, we have a few adapters implemented and available for use.
Note that some of these are plugins, meaning they require installing additional (external) libraries.

Recall to add lifecycle adapters, you just need to call the ``with_adapters`` method of the driver:

.. code-block:: python

        dr = (
            driver
            .Builder()
            .with_modules(...)
            .with_adapters(
                Adapter1(...),
                Adapter2(...),
                *more_adapters)
            ...build()
        )

.. toctree::
    PDBDebugger
    PrintLn
    ProgressBar
    RichProgressBar
    DDOGTracer
    FunctionInputOutputTypeChecker
    SlackNotifierHook
    GracefulErrorAdapter
    SparkInputValidator
    Narwhals
    MLFlowTracker
    NoEdgeAndInputTypeChecking
    OpenLineageAdapter
