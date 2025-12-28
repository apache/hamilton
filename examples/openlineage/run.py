# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import sqlite3

import pipeline
from openlineage.client import OpenLineageClient
from openlineage.client.transport.file import FileConfig, FileTransport

from hamilton import driver
from hamilton.plugins import h_openlineage

# if you don't have a running OpenLineage server, you can use the FileTransport
file_config = FileConfig(
    log_file_path="pipeline.json",
    append=True,
)

# if you have a running OpenLineage server, e.g. marquez, uncomment this line.
# client = OpenLineageClient(url="http://localhost:9000")
client = OpenLineageClient(transport=FileTransport(file_config))

ola = h_openlineage.OpenLineageAdapter(client, "demo_namespace", "my_hamilton_job")

# create inputs to run the DAG
db_client = sqlite3.connect("purchase_data.db")
# create the DAG
dr = driver.Builder().with_modules(pipeline).with_adapters(ola).build()
# display the graph
dr.display_all_functions("graph.png")
# execute & emit lineage
result = dr.execute(
    ["saved_file", "saved_to_db"],
    inputs={
        "db_client": db_client,
        "file_ds_path": "data.csv",
        "file_path": "model.pkl",
        "joined_table_name": "joined_data",
    },
)
# close the DB
db_client.close()
