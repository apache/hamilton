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

# @datasaver and @dataloader example

This example shows you can use the
`@datasaver()` and `@dataloader()` decorators to
annotated functions that save and load data so that they
can also return metadata.

This metadata is then exposed in the Apache Hamilton UI / inspectable
by other adapters.

To run this example, you can use the following command:

1. Install the requirements:
```bash
pip install -r requirements.txt
```
2. Have the Apache Hamilton UI set up. See [UI docs](https://hamilton.apache.org/hamilton-ui/) for instructions.
3. You have modified the run.py / notebook to log to the right Apache Hamilton UI project.
4. Run the example:

```bash
python run.py
```
or via the notebook.
