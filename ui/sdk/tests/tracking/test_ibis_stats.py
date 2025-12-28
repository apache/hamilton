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

import ibis
import pandas as pd
from hamilton_sdk.tracking import ibis_stats


def test_compute_stats_ibis_table():
    df = pd.DataFrame(
        [["a", 1, 2], ["b", 3, 4]],
        columns=["one", "two", "three"],
        index=[5, 6],
    )
    result = ibis.memtable(df, name="t")
    # result = Table({"a": "int", "b": "string"})
    node_name = "test_node"
    node_tags = {}
    actual = ibis_stats.compute_stats_ibis_table(result, node_name, node_tags)
    expected = {
        "observability_schema_version": "0.0.2",
        "observability_type": "dict",
        "observability_value": {
            "type": "<class 'ibis.expr.types.relations.Table'>",
            "value": {
                "columns": [
                    {
                        "base_data_type": "unhandled",
                        "data_type": "string",
                        "name": "one",
                        "nullable": True,
                        "pos": 0,
                    },
                    {
                        "base_data_type": "unhandled",
                        "data_type": "int64",
                        "name": "two",
                        "nullable": True,
                        "pos": 1,
                    },
                    {
                        "base_data_type": "unhandled",
                        "data_type": "int64",
                        "name": "three",
                        "nullable": True,
                        "pos": 2,
                    },
                ]
            },
        },
    }
    assert actual == expected
