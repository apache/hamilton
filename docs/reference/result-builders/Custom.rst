=====================
Custom ResultBuilder
=====================

If you have a use case for a custom ResultBuilder, tell us on `Slack <https://join.slack.com/t/hamilton-opensource/shared\_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg>`_
or via a `GitHub issues <https://github.com/apache/hamilton/issues/new?assignees=&labels=&projects=&template=feature_request.md&title=>`__. Knowing about your use case and talking through help ensures we aren't duplicating effort, and that it'll be using part of the API we don't intend to change.

What you need to do
-------------------

You need to implement a class that implements a single function - see \
`GitHub <https://github.com/apache/hamilton/blob/main/hamilton/base.py#L18-L28>`__:

.. code-block:: python

    class ResultBuilder(object):
        """Base class housing the result builder"""
        @abc.abstractmethod
        def build_result(self, **outputs: typing.Dict[str, typing.Any]) -> typing.Any:
            """This function builds the result given the computed values."""
            pass

For example:

.. code-block:: python

    import typing
    from hamilton import lifecycle
    class MyCustomBuilder(lifecycle.ResultBuilder):
         # add a constructor if you need to
         @staticmethod
         def build_result(**outputs: typing.Dict[str, typing.Any]) -> YOUR_RETURN_TYPE:
             """Custom function you fill in"""
             # your logic would go here
             return OBJECT_OF_YOUR_CHOOSING

How to use it
-------------

You would then have the option to pair that with a graph adapter that takes in a ResultMixin object. E.g. ``SimplePythonGraphAdapter``.
See :doc:`../graph-adapters/index` for which ones take in a custom ResultMixin object.

You can pass the result builder or a graph adapters to the ``driver.Builder(result_builder).with_adapters(...)``
function.
