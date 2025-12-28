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

# Parallelism Example

## Overview
This is a very simple example of dynamically parameterizing sections of the DAG in parallel.
This loads data from the kaggle dataset [Airbnb Prices in European Cities](https://www.kaggle.com/datasets/thedevastator/airbnb-prices-in-european-cities),
and does the following:

- Lists out the cities in the dataset See [list_data.py](list_data.py)
- Loads the files and runs a set of very basic summary statistics. See [process_data.py](process_data.py)
- Aggregates the summary into a single dataframe  See [aggregate_data.py](aggregate_data.py)

## Take home

This demonstrates two powerful capabilities:

1. Dynamically generating sets of nodes based on the result of another node
2. Running these nodes in parallel

Note that this does not do anything particularly complex -- the dataset/computation is meant to illustrate how you could use these powers.
These datasets are small and the data processing is quite simple.

## Running

First, download the data and place inside a directory called `data`.
You can download the data from [here](https://www.kaggle.com/datasets/thedevastator/airbnb-prices-in-european-cities). You'll need a kaggle account.

You can run the basic analysis in the terminal with:

```bash
python run.py
```

And you can play around with the data using the `notebook.ipynb` notebook.
