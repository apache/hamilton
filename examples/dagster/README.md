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

# Dagster + Apache Hamilton

This repository compares how to build dataflows with macro orchestrator Dagster and the micro orchestrator Apache Hamilton.

> see the [side-by-side comparison](https://hamilton.apache.org/code-comparisons/dagster/) in the Apache Hamilton documentation

## Content
- `dagster_code/` includes code from the [Dagster tutorial](https://docs.dagster.io/tutorial) to load data and compute statistics from the website [HackerNews](https://news.ycombinator.com/).
- `hamilton_code/` is a refactor of `dagster_tutorial/` using the Apache Hamilton framework.

Each directory contains instructions on how to run the code. We suggest going through the Dagster code first, then read the Apache Hamilton refactor.

## Setup
1. Create a virtual environment and activate it
    ```console
    python -m venv venv && . venv/bin/active
    ```

2. Install requirements for both Dagster and Apache Hamilton
    ```console
    pip install -r requirements.txt
    ```

3. Dagster-specific instructions are found under `dagster_code/`
