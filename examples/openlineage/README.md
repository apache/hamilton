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

# OpenLineage Adapter

This is an example of how to use the OpenLineage adapter that can be used to send metadata to an OpenLineage server.

## Motivation
OpenLineage is an open standard for data lineage.
With Apache Hamilton you can read and write data, and with OpenLineage you can track the lineage of that data.

## Steps
1. Build your project with Apache Hamilton.
2. Use one of the [materialization approaches](https://hamilton.apache.org/concepts/materialization/) to surface metadata about what is loaded and saved.
3. Use the OpenLineage adapter to send metadata to an OpenLineage server.

## To run this example:

1. Install the requirements:
```bash
pip install -r requirements.txt
```
2. Run the example:
```bash
python run.py
```
Or run the example in a notebook:
```bash
jupyter notebook
```
