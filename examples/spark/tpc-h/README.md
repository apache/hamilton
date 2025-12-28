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

# TPC-H

We've represented a few TPC-h queries using pyspark + hamilton.

While we have not optimized these for benchmarking, they provide a good set of examples for how to express pyspark logic/break
it into hamilton functions.

## Running

To run, you have `run.py` -- this enables you to run a few of the queries. That said, you'll have to generate the data on your own, which is a bit tricky.

Download dbgen here, and follow the instructions: https://www.tpc.org/tpch/. You can also reach out to us and we'll help you get set up.
