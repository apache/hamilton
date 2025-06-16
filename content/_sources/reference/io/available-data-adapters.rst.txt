========================
Using Data Adapters
========================

This is an index of all the available data adapters, both savers and loaders.
Note that some savers and loaders are the same (certain classes can handle both),
but some are different. You will want to reference this when calling out to any of the following:

1. Using :doc:`/reference/decorators/save_to/` [or for just exposing metadata :doc:`/reference/decorators/datasaver/`].
2. Using :doc:`/reference/decorators/load_from/` [or for just exposing metadata  :doc:`/reference/decorators/dataloader/`].
3. Using :doc:`materializers </reference/drivers/Driver/>`.

To read these tables, you want to first look at the key to determine which format you want --
these should be human-readable and familiar to you. Then you'll want to look at the `types` field
to figure out which is the best for your case (the object you want to load from or save to).

Finally, look up the adapter params to see what parameters you can pass to the data adapters.
The optional params come with their default value specified.

If you want more information, click on the `module`, it will send you to the code that implements
it to see how the parameters are used.

As an example, say we wanted to save a pandas dataframe to a CSV file. We would first find the
key `csv`, which would inform us that we want to call `save_to.csv` (or `to.csv` in the case
of `materialize`). Then, we would look at the `types` field, finding that there is a pandas
dataframe adapter. Finally, we would look at the `params` field, finding that we can pass
`path`, and (optionally) `sep` (which we'd realize defaults to `,` when looking at the code).

All together, we'd end up with:

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import value, save_to

    @save_to.csv(path=value("my_file.csv"))
    def my_data(...) -> pd.DataFrame:
        ...

For a less "abstracted" approach, where you just expose metadata from saving and loading, you can
annotated your saving/loading functions to do so, e.g. analogous to the above you could do:

.. code-block:: python

    import pandas as pd
    from hamilton.function_modifiers import datasaver

     def my_data(...) -> pd.DataFrame:
        # your function
        ...
        return _df  # return some df

    @datasaver
    def my_data_saver(my_data: pd.DataFrame, path: str) -> dict:
        # code to save my_data
        return {"path": path, "type": "csv", ...} # add other metadata


See :doc:`/reference/decorators/dataloader/` for more information on how to load data and expose metadata
via this more lighter weight way.

If you want to extend the `@save_to` or `@load_from` decorators, see :doc:`/reference/io/available-data-adapters` for documentation,
and `the example <https://github.com/apache/hamilton/blob/main/examples/materialization/README.md>`_
in the repository for an example of how to do so.

Note that you will need to call `registry.register_adapters` (or import a module that does that)
prior to dynamically referring to these in the code -- otherwise we won't know about them, and
won't be able to access that key!

=============
Data Loaders
=============

.. data_adapter_table:: loader

=============
Data Savers
=============

.. data_adapter_table:: saver
