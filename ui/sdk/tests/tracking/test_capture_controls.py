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

import json
from unittest.mock import Mock

import pytest

from hamilton import node
from hamilton_sdk.tracking import constants, data_observation, runs


@pytest.mark.parametrize("capture", [False, True])
def test_estimator_components_follow_data_capture_setting(monkeypatch, capture):
    sklearn_dummy = pytest.importorskip("sklearn.dummy")
    # The estimator's HTML includes its constructor parameters, even without fitting it.
    canary = "SYNTHETIC_PRIVATE_LABEL_92A7"
    estimator = sklearn_dummy.DummyClassifier(strategy="constant", constant=canary)
    model_node = node.Node("model", type(estimator), "", lambda: estimator)
    monkeypatch.setattr(constants, "CAPTURE_DATA_STATISTICS", capture)

    statistics, _, additional = runs.process_result(estimator, model_node)

    if capture:
        assert canary in json.dumps(statistics)
        assert canary in json.dumps(additional)
    else:
        assert statistics["observability_value"]["value"] == "RESULT SUMMARY DISABLED"
        assert additional == []
        assert canary not in json.dumps((statistics, additional))


@pytest.mark.parametrize("capture", [False, True])
def test_additional_introspection_is_skipped_but_schema_remains(monkeypatch, capture):
    result = object()
    result_node = node.Node("result", object, "", lambda: result)
    schema = {"observability_type": "schema", "observability_value": {"field": "str"}}
    schema_observer = Mock(return_value=schema)
    additional_observer = Mock(return_value=[{"observability_value": "payload"}])
    monkeypatch.setattr(constants, "CAPTURE_DATA_STATISTICS", capture)
    monkeypatch.setattr(data_observation, "compute_schema", schema_observer)
    monkeypatch.setattr(data_observation, "compute_additional_results", additional_observer)

    _, captured_schema, additional = runs.process_result(result, result_node)

    assert captured_schema == schema
    schema_observer.assert_called_once_with(result, result_node.name, result_node.tags)
    if capture:
        additional_observer.assert_called_once_with(result, result_node.name, result_node.tags)
        assert additional == [{"observability_value": "payload"}]
    else:
        additional_observer.assert_not_called()
        assert additional == []
