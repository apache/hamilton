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

==============================
Testing Apache Hamilton code
==============================

A common question on `Slack <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_
is "how do I test my Hamilton functions?" -- often with a worry that decorators
will get in the way. The good news: a Hamilton function is just a Python
function, so the standard ``pytest`` patterns you already know apply directly.

This guide walks through four cases, in order of increasing scope:

1. Unit-testing a plain function.
2. Unit-testing a decorated function.
3. Integration-testing the full DAG with the ``Driver``, including
   ``inputs=`` and ``overrides=``.
4. Driving an in-memory module for self-contained tests (e.g. of custom
   materializers).

The complete runnable code lives in
`examples/testing <https://github.com/apache/hamilton/tree/main/examples/testing>`_.
Every code block on this page is a ``literalinclude`` from that folder, so the
docs and the example can never drift out of sync.

Prerequisites
-------------

Install the example's dependencies and run it:

.. code-block:: bash

    cd examples/testing
    pip install -r requirements.txt
    pytest

You should see all 13 tests pass.

1. Unit-testing plain functions
-------------------------------

Hamilton encourages you to put your transformation logic in ordinary modules
that don't import the Driver. That makes them trivial to unit-test:

.. literalinclude:: ../../examples/testing/my_functions.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/my_functions.py``

Tests are just calls to the function:

.. literalinclude:: ../../examples/testing/test_my_functions.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/test_my_functions.py``

Notes
^^^^^

* No Driver is required. You import the module under test and call its
  functions like any other Python code.
* ``pytest.mark.parametrize`` is a clean way to cover edge cases without
  copy-pasting test bodies.
* Use ``pd.testing.assert_series_equal`` (or ``assert_frame_equal``) for
  pandas outputs -- it gives readable diffs on failure.

2. Unit-testing decorated functions
-----------------------------------

Hamilton's function modifiers (``@tag``, ``@parameterize``, ``@extract_columns``,
...) tell Hamilton how to wire the function into the DAG. They do **not**
change what the function does when you call it directly. You can therefore
mix two complementary techniques:

A. Call the underlying function in a unit test (cheap, fast).
B. Build a Driver and assert on the expanded DAG, to verify the wiring (slower,
   but the only way to catch decorator misuse).

The decorated module:

.. literalinclude:: ../../examples/testing/decorated_functions.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/decorated_functions.py``

The tests:

.. literalinclude:: ../../examples/testing/test_decorated_functions.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/test_decorated_functions.py``

3. Integration-testing the DAG
------------------------------

For end-to-end tests, build a Driver from the module(s) under test and call
``execute(...)`` with controlled inputs.

Two arguments are especially useful:

* ``inputs=`` injects test data at the **inputs** of the DAG -- the parameter
  names that aren't produced by any function.
* ``overrides=`` short-circuits an **intermediate** node by pinning its value.
  This is the integration-test sweet spot: instead of fabricating realistic
  raw inputs and re-deriving every intermediate, hand the DAG a known value
  for ``spend`` (or any other node) and assert on the *downstream* logic.

.. literalinclude:: ../../examples/testing/test_driver.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/test_driver.py``

Tip: ``Driver`` exposes a number of inspection methods --
``what_is_upstream_of``, ``what_is_downstream_of``, ``list_available_variables``
-- that are handy for asserting on graph shape, not just values.

4. In-memory modules for self-contained tests
---------------------------------------------

Sometimes you want a test that defines its own tiny Hamilton module inline
-- to exercise a custom materializer, regression-test a data-quality bug,
or demonstrate a pattern in a doctest. You don't need to create a new
``.py`` file; ``hamilton.ad_hoc_utils.create_temporary_module`` packages
inline-defined functions into a real module that the Driver can consume:

.. literalinclude:: ../../examples/testing/test_ad_hoc_module.py
   :language: python
   :lines: 18-
   :caption: ``examples/testing/test_ad_hoc_module.py``

This is also how Hamilton itself tests several of its built-in materializers,
so it scales up to fairly involved scenarios. See
`tests/test_ad_hoc_utils.py <https://github.com/apache/hamilton/blob/main/tests/test_ad_hoc_utils.py>`_
in the Hamilton source for more usage examples.

Where to go from here
---------------------

* Read the :doc:`/concepts/best-practices/code-organization` page -- the
  module structure it recommends is the same one that makes tests easy to
  write.
* Browse the
  `Hamilton test suite <https://github.com/apache/hamilton/tree/main/tests>`_
  for ideas; the same patterns work for user code.
* Have a testing pattern that isn't covered here? Share it on
  `Slack <https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g>`_
  -- we'd love to add it.
