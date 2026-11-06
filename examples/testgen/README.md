# Generating unit test stubs with `hamilton create-tests`

This example shows the `create-tests` CLI command, which generates
pytest-style unit test stubs for the Hamilton functions in a module.

## Steps

From this directory, with Hamilton installed:

```bash
hamilton create-tests business_logic.py
```

This writes `test_business_logic.py` next to the module with one stub per
Hamilton function:

```python
import pandas as pd
import business_logic


def test_spend_per_signup():
    spend: pd.Series = pd.Series([])  # TODO: fill in
    signups: pd.Series = pd.Series([])  # TODO: fill in
    expected = pd.Series([])  # TODO: fill in
    actual = business_logic.spend_per_signup(spend, signups)
    # comparing pandas objects: use the pandas testing module
    pd.testing.assert_series_equal(actual, expected)
...
```

Running the command again skips functions that already have a test and
appends stubs for new functions to the existing file. Use `--output/-o` to
choose a different destination file.

Run the command from an environment where the module's imports resolve; the
module's own directory is added to `sys.path` during generation so sibling
imports work.
