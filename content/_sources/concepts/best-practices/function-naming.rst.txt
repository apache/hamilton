===============
Function Naming
===============

Here are three important points about function naming:

#. It enables you to define your Apache Hamilton dataflow.
#. It drives collaboration & code reuse.
#. It serves as documentation itself.

You don't need to get this right the first time -- search and replace is really easy with Apache Hamilton code bases -- but it
is something to converge thinking on!

It enables you to define your Apache Hamilton dataflow
------------------------------------------------------

As the name of a hamilton function defines the name of the created artifact, naming is vital to a readable, extensible
hamilton codebase.  Names must mean something:

.. code-block:: python

    def foo_bar(input1: int, input2: pd.Series) -> pd.Series:
        """docs..."""
        ...

In this case, ``foo_bar`` is not helpful - it's unclear what this function produces at all. Remember you want function
names to mean something, since that will enable clarity when using Apache Hamilton, what is being requested, and will help
document what the function itself is doing.

It drives collaboration and reuse
---------------------------------

When people come to encounter your code, they'll need to understand it, add to it, modify it, etc.

You'll want to ensure some standardization to enable:

#. Mapping business concepts to function names. E.g. That will help people to find things in the code that map to things that happen within your business.
#. Ensuring naming uniformity across the code base. People usually follow the precedent of the code around them, so if everything in a particular module for say, date features, has a ``D_`` prefix, then they will likely follow that naming convention. This is likely something you will iterate on -- and it's best to try to converge on a team naming convention once you have a feel for the Hamilton functions being written by the team.

We suggest that long functions names that are separated by ``_`` aren't a bad thing. E.g. if you were to come across a
function named ``life_time_value`` versus ``ltv`` versus ``l_t_v``, which one is more obvious as to what it is and what
it represents?

It serves as documentation itself
---------------------------------

Remember your code usually lives a lot longer that you ever think it will. So our suggestion is to always err to the
more obvious way of naming to ensure it's clear what a function represents.

Again, if you were to come across a function named ``life_time_value`` versus ``ltv` versus ``l_t_v``, which one is
more obvious as to what it is and what it represents?
