===========
Decorators
===========

Apache Hamilton implements several decorators to promote business-logic deduplication, configuratibility, and add a layer of capabilities. These decorators can be found in the ``hamilton.function_modifiers`` submodule `GitHub <https://github.com/apache/hamilton/blob/main/hamilton/function_modifiers>`__.

Custom Decorators
-----------------

If you have a use case for a custom decorator, tell us on `Slack <https://join.slack.com/t/hamilton-opensource/shared\_invite/zt-1bjs72asx-wcUTgH7q7QX1igiQ5bbdcg>`_
or via a `GitHub issues <https://github.com/apache/hamilton/issues/new?assignees=&labels=&projects=&template=feature_request.md&title=>`__. Knowing about your use case and talking through help ensures we aren't duplicating effort, and that it'll be using part of the API we don't intend to change.

Reference
---------

.. toctree::
   :maxdepth: 2

   check_output
   config_when
   dataloader
   datasaver
   does
   unpack_fields
   extract_columns
   extract_fields
   inject
   load_from
   parameterize
   parameterize_extract_columns
   parameterize_frame
   parameterize_sources
   parameterize_subdag
   parameterize_values
   pipe
   resolve
   save_to
   subdag
   schema
   tag
   with_columns
