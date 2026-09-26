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

import pytest

pytest.importorskip("pyspark")

import pandas as pd  # noqa: E402
import pyspark.sql as ps  # noqa: E402

from hamilton_sdk.tracking import pyspark_stats  # noqa: E402


def test_compute_stats_pyspark():
    df = pd.DataFrame(
        [["a", 1, 2], ["b", 3, 4]],
        columns=["one", "two", "three"],
        index=[5, 6],
    )
    spark_session = ps.SparkSession.builder.getOrCreate()
    result = spark_session.createDataFrame(df)
    # result = Table({"a": "int", "b": "string"})
    node_name = "test_node"
    node_tags = {}
    actual = pyspark_stats.compute_stats_psdf(result, node_name, node_tags)
    assert actual["observability_schema_version"] == "0.0.2"
    assert actual["observability_type"] == "dict"

    observability_value = actual["observability_value"]
    assert observability_value["type"] == str(type(result))
    value = observability_value["value"]
    assert value["columns"] == [
        {
            "base_data_type": "str",
            "data_type": "string",
            "name": "one",
            "nullable": True,
            "pos": 0,
        },
        {
            "base_data_type": "numeric",
            "data_type": "long",
            "name": "two",
            "nullable": True,
            "pos": 1,
        },
        {
            "base_data_type": "numeric",
            "data_type": "long",
            "name": "three",
            "nullable": True,
            "pos": 2,
        },
    ]

    cost_explain = value["cost_explain"]
    assert "== Optimized Logical Plan ==" in cost_explain
    assert "== Physical Plan ==" in cost_explain

    extended_explain = value["extended_explain"]
    for plan_section in (
        "== Parsed Logical Plan ==",
        "== Analyzed Logical Plan ==",
        "== Optimized Logical Plan ==",
        "== Physical Plan ==",
    ):
        assert plan_section in extended_explain
    assert "one: string, two: bigint, three: bigint" in extended_explain
    spark_session.stop()
