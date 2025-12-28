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

from hamilton_sdk.tracking import pydantic_stats
from pydantic import BaseModel


class TestModel(BaseModel):
    name: str
    value: int


class TestModel2(BaseModel):
    name: str
    value: int

    def dump_model(self):
        return {"name": self.name, "value": self.value}


class EmptyModel(BaseModel):
    pass


def test_compute_stats_df_with_dump_model():
    model = TestModel2(name="test", value=2)
    result = pydantic_stats.compute_stats_pydantic(model, "node1", {"tag1": "value1"})
    assert result["observability_type"] == "dict"
    assert result["observability_value"]["type"] == str(type(model))
    assert result["observability_value"]["value"] == {"name": "test", "value": 2}
    assert result["observability_schema_version"] == "0.0.2"


def test_compute_stats_df_without_dump_model():
    model = TestModel(name="test", value=1)
    result = pydantic_stats.compute_stats_pydantic(model, "node1", {"tag1": "value1"})
    assert result["observability_type"] == "dict"
    assert result["observability_value"]["type"] == str(type(model))
    assert result["observability_value"]["value"] == {"name": "test", "value": 1}
    assert result["observability_schema_version"] == "0.0.2"


def test_compute_stats_df_with_empty_model():
    model = EmptyModel()
    result = pydantic_stats.compute_stats_pydantic(model, "node1", {"tag1": "value1"})
    assert result["observability_type"] == "dict"
    assert result["observability_value"]["type"] == str(type(model))
    assert result["observability_value"]["value"] == {}
    assert result["observability_schema_version"] == "0.0.2"
