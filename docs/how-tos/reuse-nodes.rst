..
    Licensed to the Apache Software Foundation (ASF) under one
    or more contributor license agreements.  See the NOTICE file
    distributed with this work for additional information
    regarding copyright ownership.  The ASF licenses this file
    to you under the Apache License, Version 2.0 (the
    "License"); you may not use this file except in compliance
    with the License.  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing,
    software distributed under the License is distributed on an
    "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
    KIND, either express or implied.  See the License for the
    specific language governing permissions and limitations
    under the License.

==========================================
Reusing functions and nodes
==========================================

A common question on `Slack <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_:
*"I want to run the same logic for several regions / datasets / model variants
-- what is the Hamilton way?"* Hamilton has four answers, and the right one
depends on how the variation is shaped.

This page walks through them in order from simplest to most advanced:

1. **Reuse a function module across multiple Drivers** -- the data is what
   varies, the dataflow is the same.
2. **Override a module with another that has the same function names** --
   one or two specific functions need to be swapped (e.g. for testing or for a
   different runtime context).
3. **Use** ``@subdag`` -- you want the *same* transformation graph evaluated
   several times *inside one Driver*, with different inputs or config.
4. **Use** ``@parameterized_subdag`` -- the variation is large enough that
   writing one ``@subdag`` per case becomes tedious. (Advanced.)

Every code sample below is taken from a runnable example in the
`examples folder <https://github.com/apache/hamilton/tree/main/examples>`_, so
you can copy any of them, run them locally, and adapt them.


1. Reuse a function module across multiple Drivers
--------------------------------------------------

If the *dataflow* is the same and only the *data* changes, you do not need
any decorator -- you just import the function module and build a Driver
wherever you need one. This is the most common form of reuse and the one to
reach for first.

The
`feature_engineering_multiple_contexts <https://github.com/apache/hamilton/tree/main/examples/feature_engineering/feature_engineering_multiple_contexts>`_
example shows this pattern across an offline ETL and an online FastAPI
service: ``features.py`` is written **once**, then driven from two contexts.
The offline ETL builds a Driver and executes it on a batch of rows; the
online server builds another Driver from the same module and executes it
per-request.

When to reach for this pattern:

* The same feature definitions need to run in batch *and* in a request
  handler.
* You want to share code between training and inference.
* You want different teams to consume the same canonical module with their
  own inputs.

What you do *not* need: any Hamilton-specific decorator. The reuse is just
ordinary Python imports plus building a Driver per context.


2. Override a module to swap same-named functions
-------------------------------------------------

Sometimes you want most of a dataflow to stay the same and only swap one
or two functions -- for example, replacing a real data loader with a mock
one in tests, or switching between two implementations of the same business
rule.

By default Hamilton refuses to build a DAG when two modules define
functions with the same name, because the resulting graph would be
ambiguous. The
`module_overrides <https://github.com/apache/hamilton/tree/main/examples/module_overrides>`_
example shows how to opt in to a "later wins" rule with
``Builder.allow_module_overrides()``:

.. literalinclude:: ../../examples/module_overrides/module_a.py
   :language: python
   :lines: 19-
   :caption: ``examples/module_overrides/module_a.py``

.. literalinclude:: ../../examples/module_overrides/module_b.py
   :language: python
   :lines: 19-
   :caption: ``examples/module_overrides/module_b.py``

.. literalinclude:: ../../examples/module_overrides/run.py
   :language: python
   :lines: 18-
   :caption: ``examples/module_overrides/run.py``

When ``allow_module_overrides()`` is set, the function from the
**later-imported** module wins, so the example above prints
``"This is module b."``.

When to reach for this pattern:

* You have a stable dataflow but want a small, well-named seam for swapping
  in a test double, a mock data source, or an environment-specific function.
* You want the swap to be visible in the Driver-construction code, rather
  than buried inside a function or a config flag.

When *not* to reach for this pattern:

* If many functions need to vary, prefer keeping the variations in distinct
  modules and choosing which one to import. Module overrides are best as a
  surgical tool.


3. ``@subdag`` -- repeat the same transform inside one Driver
-------------------------------------------------------------

Sometimes you want the *same* transformation graph evaluated several times
*inside the same DAG*, each time with a different input or configuration --
for example, computing unique-user counts at daily / weekly / monthly grains
across two regions.

The ``@subdag`` decorator from ``hamilton.function_modifiers`` does this
declaratively. From the source documentation:

    ``@subdag`` enables you to rerun components of your DAG with varying
    parameters. That is, it enables you to "chain" what you could express
    with a Driver into a single DAG.

The
`reusing_functions <https://github.com/apache/hamilton/tree/main/examples/reusing_functions>`_
example computes ``unique_users`` for two regions and three time grains.
The shared logic lives in ``unique_users.py``:

.. literalinclude:: ../../examples/reusing_functions/unique_users.py
   :language: python
   :lines: 18-
   :caption: ``examples/reusing_functions/unique_users.py``

Then in ``reusable_subdags.py``, each ``@subdag`` declaration creates one
named instance of that subgraph, with its own ``inputs`` and ``config``:

.. literalinclude:: ../../examples/reusing_functions/reusable_subdags.py
   :language: python
   :pyobject: daily_unique_users_US
   :caption: One @subdag invocation from ``examples/reusing_functions/reusable_subdags.py``

Each decorated function:

* Takes the *output* of its sub-DAG as its argument. Above, the sub-DAG ends
  in ``unique_users``, so the wrapping function receives ``unique_users:
  pd.Series`` and returns it (perhaps after post-processing).
* Receives ``inputs={"grain": value("day")}`` -- this binds the sub-DAG
  input ``grain`` to the literal ``"day"`` for *this instance only*.
* Receives ``config={"region": "US"}`` -- this scopes Hamilton's
  ``@config.when`` selection to ``"US"`` for this sub-DAG.

The same module then defines five more analogous functions (``weekly_*``,
``monthly_*``, the ``CA`` variants), giving twelve nodes that all reuse the
same underlying definitions.

Two parameters worth knowing:

* ``namespace`` -- a string prefix for the nodes that ``@subdag`` materialises.
  By default Hamilton uses the wrapping function's name, which is normally
  what you want.
* ``external_inputs`` -- declare any function parameter that comes from
  *outside* the sub-DAG (e.g. from the surrounding DAG). This makes the
  boundary between the sub-DAG and its surroundings explicit.

When to reach for this pattern:

* You want one Driver, one visualised DAG, and one ``execute`` call to
  produce all the variants -- rather than a Python ``for`` loop over many
  Drivers in your application code.
* You want lineage and execution metadata for every variant captured by
  Hamilton, not by a wrapper script.


4. ``@parameterized_subdag`` -- many subdags at once (advanced)
---------------------------------------------------------------

If you have *many* subdags that differ only along a small number of
parameters, writing one ``@subdag`` declaration per case becomes verbose.
``@parameterized_subdag`` is syntactic sugar that produces several subdags
from a single decorator -- analogous to how ``@parameterize`` produces
several nodes from one function.

From the
`source documentation <https://github.com/apache/hamilton/blob/main/hamilton/function_modifiers/recursive.py>`_:

.. code-block:: python

    @parameterized_subdag(
        feature_modules,
        from_datasource_1={"inputs": {"data": value("datasource_1.csv")}},
        from_datasource_2={"inputs": {"data": value("datasource_2.csv")}},
        from_datasource_3={
            "inputs": {"data": value("datasource_3.csv")},
            "config": {"filter": "only_even_client_ids"},
        },
    )
    def feature_engineering(feature_df: pd.DataFrame) -> pd.DataFrame:
        return feature_df

Each entry below the decorator becomes one subdag, all built from the same
``feature_modules`` but with different inputs / config.

The Hamilton source itself includes a deliberate warning on this decorator:

    Think about whether this feature is really the one you want -- often
    times, verbose, static DAGs are far more readable than very concise,
    highly parameterized DAGs.

In practice: prefer the explicit form from section 3 until the repetition
genuinely hurts. Reach for ``@parameterized_subdag`` when the parameter
list comes from elsewhere (e.g. a config file resolved with ``@resolve``)
or when you have a dozen-plus near-identical subdags.

The full reference for both decorators lives at:

* :doc:`/reference/decorators/subdag`
* :doc:`/reference/decorators/parameterize_subdag`


Choosing between the four patterns
----------------------------------

A short decision tree:

* **The data varies, the code does not** → just build another Driver from
  the same module (section 1).
* **One or two named functions need to be swapped** → put the swaps in
  another module and use ``allow_module_overrides()`` (section 2).
* **You want N copies of the same transform graph in one DAG** → use
  ``@subdag`` (section 3).
* **You have many copies and the parameter list is itself data** → consider
  ``@parameterized_subdag`` (section 4).

In practice, most production Hamilton projects rely heavily on (1), use (2)
sparingly for testing seams, reach for (3) when modeling per-segment or
per-grain pipelines, and treat (4) as an advanced tool.


Where to go from here
---------------------

* Walk through the runnable examples linked above:
  `feature_engineering_multiple_contexts <https://github.com/apache/hamilton/tree/main/examples/feature_engineering/feature_engineering_multiple_contexts>`_,
  `module_overrides <https://github.com/apache/hamilton/tree/main/examples/module_overrides>`_,
  and
  `reusing_functions <https://github.com/apache/hamilton/tree/main/examples/reusing_functions>`_.
* Read :doc:`/concepts/best-practices/code-organization` for the module
  layout that makes these patterns natural.
* For an end-to-end deep-dive on subdags and reuse, see the
  `Hamilton March 2024 Meetup tutorial notebook <https://github.com/DAGWorks-Inc/hamilton-tutorials/blob/main/2024-03-19/march-meetup.ipynb>`_.
