<!--
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
-->

# Testing Apache Hamilton code

This is the runnable companion to the
[Testing Hamilton code](https://hamilton.apache.org/how-tos/test-hamilton-code/)
how-to. It shows that Hamilton functions are normal Python -- so the standard
`pytest` patterns you already know apply, including when decorators are
involved.

The example covers the four cases from issue
[#1044](https://github.com/apache/hamilton/issues/1044):

1. **Unit-testing plain functions** -- `test_my_functions.py`
2. **Unit-testing decorated functions** -- `test_decorated_functions.py`
3. **Integration-testing the DAG with `inputs=` and `overrides=`** -- `test_driver.py`
4. **In-memory modules with `ad_hoc_utils.create_temporary_module`** -- `test_ad_hoc_module.py`

## File organization

| File | Purpose |
| ---- | ------- |
| `my_functions.py` | A small marketing dataflow (no decorators). |
| `decorated_functions.py` | The same style of dataflow, using `@tag`, `@parameterize` and `@extract_columns`. |
| `test_my_functions.py` | Unit tests that import and call functions directly. |
| `test_decorated_functions.py` | Unit + driver-level tests for the decorated module. |
| `test_driver.py` | End-to-end tests using `Builder().with_modules(...).build()` plus `inputs=` and `overrides=`. |
| `test_ad_hoc_module.py` | Builds a module from inline-defined functions for self-contained tests. |
| `conftest.py` | Adds this folder to `sys.path` so `import my_functions` works under pytest. |

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

You should see all tests pass. Each test file is independently runnable:

```bash
pytest test_my_functions.py -v
pytest test_driver.py -v
```

## What to take away

* A Hamilton function is just a Python function. Testing it does **not**
  require building a Driver.
* Decorators (`@tag`, `@parameterize`, `@extract_columns`, ...) leave the
  underlying callable intact. Direct function calls still work; the decorator
  changes how Hamilton wires the function into the DAG, not what the function
  computes.
* For integration tests, `Builder().with_modules(...).build()` is the canonical
  entry point. Use `inputs=` to inject test data at the DAG inputs and
  `overrides=` to short-circuit intermediate nodes when you want to assert on
  downstream logic in isolation.
* Need to test inline -- e.g. for a regression test or a custom materializer
  -- without a `.py` file on disk? Use
  `hamilton.ad_hoc_utils.create_temporary_module`.

If you have questions, or need help with this example,
join us on [Slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g).
