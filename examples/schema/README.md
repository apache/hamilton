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

# Schema tracking and validation

This examples showcases the `SchemaValidator()` adapter. At runtime, it will collect the schema of DataFrame-like objects and stored them as `pyarrow.Schema` objects. On subsequent runs, it will check if the schema of a noed output matches the stored reference schema.

## Content
## Simple example
- `dataflow.py` defines a dataflow with 3 nodes returning pandas `DataFrame` objects. The `SchemaValidator` added to the `Builder` automatically tracks their schema. After running it once, next runs will check the schema against the schemas stored on disk.
- `/schemas` includes the stored `.schema` files. They are created using the standard IPC Arrow serialization format. Unfortunately, they are not human readable. We produce a readable `schemas.json` with all the original schema and metadata. We'll be improving it's readability over time.

### Multi library example
- `multi_dataflow.py` defines a dataflow with 3 nodes returning pyarrow, ibis, and pandas dataframes and use the `SchemaValidator()` to track their schema. After running it once, you can change the `Driver` config to use `version="2"` and see the schema validation fail.
- `/multi_schemas` includes similar content as `/schemas`

You can play with the arguments `--version [1, 2, 3]` and `--no-check` to update the stored schema, trigger failing schema checks, and view the diffs.

## Output examples
### Diff examples
```python
{'col_b': 'added'}
{'col_a': {'type': 'bool -> double'}}
{'col_b': 'removed', 'col_a': {'type': 'bool -> double'}}
```

### Default Pyarrow schema display
```python
{'pyarrow_table': item: string
value: decimal128(10, 2)
count: int32
-- schema metadata --
name: 'pyarrow_table'
documentation: 'Create a duckdb table in-memory and return it as a PyArro' + 7
version: 'cc8d5aba6219976c719ef0c7ac78065aef8a6c7612ea1c3ff595d0892660346' + 1, 'ibis_rename': object: string
price: decimal128(10, 2)
number: int32
-- schema metadata --
name: 'ibis_rename'
documentation: 'Rename the columns'
version: '31a5e44b3b718f994865e589642a555fee5db44ba86eaa3bcc25bc9f4242389' + 1, 'pandas_new_col': object: string
price: decimal128(4, 2)
number: int32
col_a: double
-- schema metadata --
name: 'pandas_new_col'
documentation: 'Add the column `new_col` of type float'
version: '7c679d7dbe665b55b8157f3c0a3962ea26aa0a3f6edaea44120374e33c58acb' + 1}
```

### Human-readable and JSON-serializable schema
```python
{
  "pyarrow_table": {
    "metadata": {
      "name": "pyarrow_table",
      "documentation": "Create a duckdb table in-memory and return it as a PyArrow table",
      "version": "cc8d5aba6219976c719ef0c7ac78065aef8a6c7612ea1c3ff595d08926603467"
    },
    "item": {
      "name": "item",
      "type": "string",
      "nullable": true,
      "metadata": null
    },
    "value": {
      "name": "value",
      "type": "decimal128(10, 2)",
      "nullable": true,
      "metadata": null
    },
    "count": {
      "name": "count",
      "type": "int32",
      "nullable": true,
      "metadata": null
    }
  },
  "ibis_rename": {
    "metadata": {
      "name": "ibis_rename",
      "documentation": "Rename the columns",
      "version": "31a5e44b3b718f994865e589642a555fee5db44ba86eaa3bcc25bc9f42423895"
    },
    "object": {
      "name": "object",
      "type": "string",
      "nullable": true,
      "metadata": null
    },
    "price": {
      "name": "price",
      "type": "decimal128(10, 2)",
      "nullable": true,
      "metadata": null
    },
    "number": {
      "name": "number",
      "type": "int32",
      "nullable": true,
      "metadata": null
    }
  },
  "pandas_new_col": {
    "metadata": {
      "name": "pandas_new_col",
      "documentation": "Add the column `new_col` of type float",
      "version": "7c679d7dbe665b55b8157f3c0a3962ea26aa0a3f6edaea44120374e33c58acbd"
    },
    "object": {
      "name": "object",
      "type": "string",
      "nullable": true,
      "metadata": null
    },
    "price": {
      "name": "price",
      "type": "decimal128(4, 2)",
      "nullable": true,
      "metadata": null
    },
    "number": {
      "name": "number",
      "type": "int32",
      "nullable": true,
      "metadata": null
    },
    "col_a": {
      "name": "col_a",
      "type": "double",
      "nullable": true,
      "metadata": null
    }
  }
}
```
