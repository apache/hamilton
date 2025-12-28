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

# Dask Community day demo example

This example was demo'ed at the Dask community day for July 2023.

In this example we showcase using the [Apache Hamilton DaskGraphAdapter](https://hamilton.apache.org/reference/graph-adapters/DaskGraphAdapter/#h-dask-daskgraphadapter)
to inject dask.delayed() as it's walking the DAG that is defined with Apache Hamilton.

File organization:

* `my_functions.py` houses the logic that we want to compute. Note how the functions are named, and what input
parameters they require. That is how we create a DAG modeling the dataflow we want to happen.
* `demo_day_notebook.ipynb` is the notebook that was shown in the demo. At the top it shows using Apache Hamilton, and running
the code without delegating to Dask, and then at the bottom it shows how to use the DaskGraphAdapter that augments
how the DAG is walked, because it calls dask.delayed on every function.

To run things, open up the notebook and run it, after installing the requisite dependencies:
```bash
pip install -r requirements.txt
jupyter notebook
```

Or run it in Google Colab:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/dask/community_demo/demo_day_notebook.ipynb)



If you have questions, or need help with this example,
join us on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g), and we'll try to help!

# What is executed
This is a simple DAG that we construct here. But for reference it looks like this:
![my_dag](my_dag.dot.png)

# References:
* [Dask](https://dask.org/)
* [Apache Hamilton Docs](https://hamilton.apache.org/)
* [Try Apache Hamilton in your browser](https://www.tryhamilton.dev/)
