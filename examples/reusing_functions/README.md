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

# subdag operator

This README demonstrates the use of the subdag operator.

The subdag operator allows you to effectively run a driver within a node.
In this case, we are calculating unique website visitors from the following set of parameters:

1. Region = CA (canada) or US (United States)
2. Granularity of data = (day, week, month)

You can find the code in [unique_users.py](unique_users.py) and [reusable_subdags.py](reusable_subdags.py)
and look at how we run it in [main.py](main.py).

# Visualizing Execution
Here you can see the resulting shape of the DAG that will be executed:

![reusable_subdags](reusable_subdags.png)
