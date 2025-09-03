# Read carefully

> Use at your own risk

This directory contains code for the package `sf-hamilton-core`. It is a drop-in replacement of `sf-hamilton`, with two changes:
- disable plugin autoloading
- make `pandas` and `numpy` optional dependencies; and remove `networkx` dependency (currently unused).

This makes the Hamilton package a much lighter install and solves long library loading time.

## As a user
If you want to try `sf-hamilton-core`, you need to:
1. Remove your current Hamilton installation: `pip uninstall sf-hamilton`
2. Install Hamilton core `pip install sf-hamilton-core`
3. Check installation `pip list` should only include `sf-hamilton-core`.

This will install a different Python package with the name `hamilton` with the smaller dependencies and plugin autoloading disabled.

It should be a drop-in replacement and your existing Hamilton code should just work. Though, if you're relying on plugins (e.g., parquet materializers, dataframe result builders), you will need to manually load them.


## How does it work


## Why is another package `sf-hamilton` necessary
This exists to prevent backwards incompatible changes for people who `pip install sf-hamilton` and use it in production. It is a temporary solution until a major release `sf-hamilton==2.0.0` could allow breaking changes and a more robust solution.

### Disable plugin autoloading
Hamilton has generous number of plugins (`pandas`, `polars`, `mlflow`, `spark`). To give a good user experience, Hamilton autoloads plugins based on the available Python libraries in the current Python environment. For example, `to.mlflow()` becomes available if `mlflow` is installed. Autoloaded features notably include materializers like `from_.parquet` and `to.parquet` and data validators (pydantic, pandera, etc.)

The issue with this approach is that Python environment with a lot of dependencies, common in data science, can be very slow to start because of all the imports. Currently, Hamilton allows to disable autoloading via a user config or Python code. This require manual setups and is not the best default for some users.

### `pandas` and `numpy` dependencies
Hamilton was initially created for workflows that used `pandas` and `numpy` heavily. For this reason, `numpy` and `pandas` are imported at the top-level of module `hamilton.base`. Because of the package structure, as a Hamilton user, you're importing `pandas` and `numpy` every time you import `hamilton`.

A reasonable change would be to move `numpy` and `pandas` to a "lazy" location. Then, dependencies would only be imported when features requiring them are used and they could be removed from `pyproject.toml`. Unfortunately, plugin autoloading defaults make this solution a significant breaking change and insatisfactory.

Since plugins are loaded based on the Python package available, removing `pandas` and `numpy` would allow disable the loading of these plugins. This would break popular CSV and parquet materializers.

### `networkx` dependency
The `sf-hamilton[visualization]` extra currently includes `networkx` as a dependency, though it is never actually used. There's a single function requiring it and it could be implemented in pure Python. This has been made even easier with the addition of `graphlib` in the standard library in Python 3.9.
