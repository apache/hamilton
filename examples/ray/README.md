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

# Scaling Apache Hamilton on Ray

[Ray](https://ray.io) is a general purpose framework that allows for parallel
computation on a local machine, as well as scaling to a
Ray cluster.

# Two ways to use Ray

## injecting @ray.remote
See the `hello_world` example for how you might accomplish
scaling Apache Hamilton on Ray, where `@ray.remote` is injected around
each Apache Hamilton function.

## creating tasks
For [this paralle task approach](https://hamilton.apache.org/concepts/parallel-task/) see [this
example](https://github.com/apache/hamilton/tree/main/examples/LLM_Workflows/scraping_and_chunking) instead.
