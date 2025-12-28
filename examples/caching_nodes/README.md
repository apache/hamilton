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

# Caching

There are four general approaches to caching in Apache Hamilton.

1. You do it yourself outside of Apache Hamilton and use the [`overrides`](https://hamilton.apache.org/reference/drivers/#short-circuiting-some-dag-computation) argument in `.execute/.materialize(..., overrides={...})` to inject pre-computed values into the graph. That is, you run your code, save the things you want, and then you load them and inject them using `overrides=`. TODO: show example.
2. You use the data savers & data loaders. This is similar to the above, but instead you use the [Data Savers & Data Loaders (i.e. materializers)](https://hamilton.apache.org/reference/io/available-data-adapters/) to save & then load and inject data in. TODO: show example.
3. You use the `CachingGraphAdapter`, which requires you to tag functions to cache along with the serialization format.
4. You use the `DiskCacheAdapter`, which uses the `diskcache` library to store the results on disk.

All approaches have their sweet spots and trade-offs. We invite you play with them and provide feedback on which one you prefer.
