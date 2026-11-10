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

Running the command again skips functions that already have a test and appends
stubs for new functions to the existing file. Use `--output/-o` to choose a
different destination file.

If the existing file cannot be parsed as Python, the command reports an error
and leaves it untouched rather than appending to it.

Imports are added when the new stubs need them, above the first line of code in
the file. The stubs call `pd.*` and `<module>.function(...)`, so the generator
adds exactly what binds those names: a file that only had
`from pandas import Series` or `import pandas as pandas_alias` gains
`import pandas as pd`, and a file that imported the module under another alias
gets `import pkg.mod` as well.

Signatures are read from the module's source with `ast`, so generating stubs
never imports the module and no top-level code of it runs at generation time.
(The generated test file does import it later, when the tests run, so its
top-level code runs then as it would for any test.) Modules that use
package-relative imports are fine too: a module inside a regular package (a
directory with an `__init__.py`) is imported by its dotted path, so
`pkg/orders.py` generates `import pkg.orders` and calls
`pkg.orders.total_spend(...)`. Only that layout is detected: namespace packages
are not, and the generated import is relative to the package root, so run the
tests from a checkout that has that root on `sys.path`.

Generated calls keep each parameter's kind, and every parameter is passed, so
the stub always runs the function with the values written above it. It is a
stub: a parameter whose default is omitted on purpose in the real call is still
passed here, so the default is not exercised until you edit the stub.

```python
# business_logic.py
def total_spend(period: str, /, *, include_tax: bool = False, **filters):
    ...

# generated stub
def test_total_spend():
    period = None  # TODO: fill in
    include_tax = False  # TODO: fill in
    filters = {}  # TODO: fill in
    actual = business_logic.total_spend(period, include_tax=include_tax, **filters)
```

If a default is not something the stub can carry in-line, such as
`def bump(level=DEFAULT_LEVEL)`, the stub leaves the original in the comment
instead of writing a name it has not imported:

```python
    level = None  # TODO: fill in (default is DEFAULT_LEVEL)
```

The same rule applies to annotations the generated file cannot resolve, such as
one that needs `typing`; it becomes part of the comment and the parameter is left
unannotated. Only synchronous module-level functions get stubs: an `async def`
would need a test that awaits it, which the command does not assume.
