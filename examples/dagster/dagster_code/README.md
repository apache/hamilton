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

# Dagster

This project is adapted from the official [Dagster tutorial](https://docs.dagster.io/tutorial).

## File structure
- `tutorial/` is a Python module that contains our Dagster project. It needs to be installed in our Python environment.
- `pyproject.toml` and `setup.py` define how to install the `tutorial/` Dagster project.
- `tutorial/assets.py` defines the data assets to compute and materialize.
- `tutorial/__init__.py` register the data assets, jobs, and resources for the orchestrator.
- `tutorial/resources/` contains informations to connect to external resources and API.

## Instructions
1. Install the Dagster project as a Python module
    ```console
    pip install -e .
    ```
2. Launch the Dagster UI
    ```console
    dagster dev
    ```
3. Access Dagster UI via the generated link (default: http://127.0.0.1:3000)
