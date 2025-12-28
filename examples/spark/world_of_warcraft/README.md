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

# Example Feature Pipeline for both Spark and Pandas

This folder contains code to create features from World of Warcraft data.
The same example is created for both spark and pandas.

To get started first download the data:
`curl https://storage.googleapis.com/shareddatasets/wow.parquet -o data/wow.parquet`

## Spark example V1 vs V2

For the spark example we've created two different versions which both have their benefits and drawbacks.
See the notebooks for the details. The high level differences are as follows.

### Spark example V1
Keeps the code simpler (shorter) at the cost of losing column-level lineage.

### Spark example V2
Needs more lines of code (added complexity) but makes it easier to test and track (lineage) single transformations.
