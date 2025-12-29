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

# Plugins

Apache Hamilton enables plugins -- the requirement is that the core library according to the plugin is installed, and the plugin will be registered automatically.
It is up to the user to install the plugin via the target, E.G. `hamilton[pyspark]`, which will install the correct depdendencies.


## Structure

For each plugin, `foo`, there will be two files (likely, at some point, broken into modules), that will have the names:
1. `foo_extensions.py` This refers to constructs that get automatically registered (dataframe/column types, data loaders, etc...) This never gets imported by the user directly.
2. `h_foo.py` This refers to constructs that the user refers to directly, E.G. specific decorators, result builders, etc...

`h_foo` is just another module. `foo_extensions` has a few special properties.

1. It can opt out of specifying dataframe/column types if it doesn't make sense, by containing the variable `COLUMN_FRIENDLY_DF_TYPE = False`. This defaults to true on import.
2. If it is true, it must contain the following methods:
   1. `get_column_foo` -- a function to extract the column
   2. `register_types` -- a function to register the types for that extension
   3. `fill_with_scalar_foo` -- a function to fill a column with a scalar

`register_types` must be called within the module body, as must registering any data loaders. This restriction will likely be removed and the registering pulled out to import level.

Note this is not a public-facing API -- this is for managing internal plugins. If you want to add new capabilities, feel free to reach out to the team.


## Adding a new plugin

Follow the rules above. Also add an install target with the same name in `setup.py`. Once you add this, you'll also want to update [registry.py](../registry.py) to include the new plugin, and update
the [docs](../../docs/data_adapters_extension.py) to document it.
