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

# Caching Graph Adapter

You can use `CachingGraphAdapter` to cache certain nodes.

This is great for:

1. Iterating during development, where you don't want to recompute certain expensive function calls.
2. Providing some lightweight means to control recomputation in production, by controlling whether a "cached file" exists or not.

For iterating during development, the general process would be:

1. Write your functions.
2. Mark them with `tag(cache="SERIALIZATION_FORMAT")`
3. Use the CachingGraphAdapter and pass that to the Driver to turn on caching for these functions.
    a. If at any point in your development you need to re-run a cached node, you can pass
       its name to the adapter in the `force_compute` argument. Then, this node and its downstream
       nodes will be computed instead of loaded from cache.
4. When no longer required, you can just skip (3) and any caching behavior will be skipped.

To exercise this example you can run it in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)
](https://colab.research.google.com/github/dagworks-inc/hamilton/blob/main/examples/caching_nodes/caching_graph_adapter/caching_nodes.ipynb)
