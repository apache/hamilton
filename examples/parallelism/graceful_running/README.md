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

# Parallelism with GracefulErrorAdapter Example

## Overview

This is a simple example of using the `GracefulErrorAdapter` in a parallelism example, where we might expect some component of an analysis to fail, but we'd still like to get as much data back as we can.

This example divides a large dataframe into smaller frames, and runs the same analysis on each of those frames. It then gathers the results at the end into a single frame. Any errors inside the paralellism block do not halt the total operation of the driver.

The user can define custom data splitting functions to process in the same sub-dag. In some ways, this is an example of how to do `@subdag` with `Parallelizable`.

The DAG is shown below, which is a simple set of operations on a custom set of splits of a dataframe. Failures occur on purpose in this example in the `model_fit` portion.

![image](dag.png)

## Take home

This demonstrates these capabilities:

1. Dynamically generating datasets from a larger one and analyzing them the same way - in parallel
2. Skipping over nodes when a failure occurs and returning sentinel values on failure

## Running

You can run the basic analysis in the terminal with:

```bash
python run.py
```

Change the `mode` input to demonstrate multiple methods of running in parallel.

Add the flag `--no-adapt` to see the failure that occurs when not using the adapter.

Modify the example to throw an exception in a function passed in to split the data. Change the order of the functions to see the effect on the results.
