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

# Apache Hamilton on Ray

Here we have a hello world example showing how you can
take some Apache Hamilton functions and then easily run them
in a distributed setting via ray.

`pip install sf-hamilton[ray]`  or `pip install sf-hamilton ray` to for the right dependencies to run this example.

File organization:

* `business_logic.py` houses logic that should be invariant to how hamilton is executed.
* `data_loaders.py` houses logic to load data for the business_logic.py module. The
idea is that you'd swap this module out for other ways of loading data.
* `run.py` is the script that ties everything together that uses vanilla Ray.

# Running the code:
For the vanilla Ray implementation use:

> python run.py

Here is the visualization of the execution:

![ray_dag](ray_dag.png)
