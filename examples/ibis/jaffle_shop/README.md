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

# Jaffle shop

This repository is a reimplementation of the canonical [dbt example jaffle_shop](https://github.com/dbt-labs/jaffle_shop). It illustrates data transformations for an ecommerce store.

Data transformations are implemented using the Python library [Ibis](https://ibis-project.org/) which allows to define SQL operations that works across backends. By default, it uses [duckdb](https://duckdb.org/) for local development. Apache Hamilton + Ibis provides a Python-centric alternative to dbt ([Learn more](https://hamilton.apache.org/integrations/ibis/)).

## Content
The content and structure aims to match the [original dbt `jaffle_shop`](https://github.com/dbt-labs/jaffle_shop/tree/main) example. On the other hand, Apache Hamilton is just a Python library and is flexible regarding project structure.

- `data/`: samples data; equivalent to `seeds/` in the dbt repo.
- `dataflows/staging` load raw data and rename columns to avoid naming conflicts; equivalent to `models/staging/` in the dbt repo.
- `dataflows/customer_flow.py` and `dataflows/order_flow.py` define data transformations; equivalent to `models/customers.sql` and `models/orders.sql` in the dbt repo.
- `run.py` specify where to load data from and how to execute dataflows.

 Generally, you'll notice Apache Hamilton aims to reduce the sprawl of configurations (`.yaml`) and documentation (`.md`). Instead, it uses docstrings, type hints, or Python object to couple them to with your code (`.py`).

## Set up
1. create and activate virtual environment

    ```script
    python -m venv venv & . venv/bin/activate
    ```
2. install requirements

    ```script
    pip install -r requirements.txt
    ```

3. execute the Apache Hamilton dataflow

    ```script
    python run.py
    ```

## Resources
Jaffle shop is an example used by many different frameworks, which can ground comparisons between each other.

- dbt: https://github.com/dbt-labs/jaffle_shop/blob/main/models/orders.sql
- dbt + duckdb: https://github.com/dbt-labs/jaffle_shop_duckdb
- Kedro: https://github.com/deepyaman/jaffle-shop/blob/main/src/jaffle_shop/pipelines/data_processing/nodes.py
- Dagster: https://github.com/stkbailey/dagster-jaffle-shop
