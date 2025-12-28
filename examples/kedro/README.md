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

# Kedro & Apache Hamilton

This repository compares how to build dataflows with Kedro and Apache Hamilton.

> see the [side-by-side comparison](https://hamilton.apache.org/code-comparisons/kedro/) in the Apache Hamilton documentation

## Content
- `kedro-code/` includes code from the [Kedro Spaceflight tutorial](https://docs.kedro.org/en/stable/tutorial/tutorial_template.html).
- `hamilton-code/` is a refactor of `kedro-code/` using the Apache Hamilton library.
- `kedro-plugin/` showcases Apache Hamilton plugins to integrate with the Kedro framework.

Each directory contains a `README` with instructions on how to run the code. We suggest going through the Kedro code first, and then read the Apache Hamilton refactor.
