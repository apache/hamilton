# Star counting with Apache Hamilton/Parallelism

This example goes along with the "Counting Stars with Apache Hamilton" blog post.

# Running

To get started, you can either open up notebook.ipynb to run, or execute `run.py`.

```bash
python run.py --help
/Users/elijahbenizzy/.pyenv/versions/hamilton/lib/python3.9/site-packages/pyspark/pandas/__init__.py:50: UserWarning: 'PYARROW_IGNORE_TIMEZONE' environment variable was not set. It is required to set this environment variable to '1' in both driver and executor sides if you use pyarrow>=2.0.0. pandas-on-Spark will set it for you but it does not work if there is a Spark context already launched.
  warnings.warn(
Usage: run.py [OPTIONS]

Options:
  -k, --github-api-key TEXT       Github API key -- use from a secure storage
                                  location!.  [required]
  -r, --repositories TEXT         Repositories to query from. Must be in
                                  pattern org/repository
  --mode [local|multithreading|dask|ray]
                                  Where to run remote tasks.
  --help                          Show this message and exit.
```
