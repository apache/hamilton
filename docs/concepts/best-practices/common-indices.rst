==============
Common Indices
==============

If you're creating dataframes, then this will apply to you!

While Apache Hamilton is a general-purpose framework, we've found a common pattern is to manipulate datasets that have shared
indices (spines) for creating dataframes.

Although this might not apply towards every use-case (E.G. more complex joins with spark dataframes), a large selection
of use-cases can be enabled if every dataframe in your pipeline shares an index. This is particularly pertinent when
writing transformations over (non-event-based) time-series data.

While Apache Hamilton currently has no means of enforcing shared-spine, it is up to the writer of the function to validate
input data as necessary. Thus we recommend the following if you are creating a dataframe as output:

Best practice:
--------------

#. Load data via functions, defined in their own specific module.
#. Take that loaded data, and transform/ensure indexes match the output you want to create.
#. Continue with transformations.

For time-series modeling, this will mean you provide a common time-series index. Or, if you're creating features for
input to a classification model, e.g. over clients, then ensure the index is client\_ids.
