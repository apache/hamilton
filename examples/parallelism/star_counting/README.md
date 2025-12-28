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
