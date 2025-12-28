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

# Example showing graph validation

This uses the StaticValidator class to validate a graph.

This specifically show how, for example, you can validate tags on functions.

 - run.py shows the validator and how to wire it in
 - good_module.py shows a node with the correct tags
 - bad_module.py shows a node with the wrong tags
 - notebook.ipynb shows how to run the same code in a notebook

To run the example, run `python run.py` and you should see the following output:

```
# good_module.py ran
{'foo': 'Hello, world!'}

# bad_module.py didn't have the right tags so graph building errored out
...
Apache Hamilton.lifecycle.base.ValidationException: Node validation failed! 1 errors encountered:
  foo: Node bad_module.foo is an output node, but does not have a table_name tag.
```

Alternatively you can run this all via the notebook.ipynb.
