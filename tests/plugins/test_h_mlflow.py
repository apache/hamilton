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

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("mlflow")

from hamilton import graph_types
from hamilton.plugins.h_mlflow import MLFlowTracker


@patch("hamilton.plugins.h_mlflow.mlflow")
def test_mlflow_tracker_none_inputs_config(mock_mlflow):
    tracker = MLFlowTracker(experiment_name="test")
    tracker.client = MagicMock()

    dummy_graph = MagicMock(spec=graph_types.HamiltonGraph)
    dummy_graph.version = "1.0"
    dummy_graph.nodes = []
    tracker.config = None

    tracker.run_before_graph_execution(
        run_id="1", final_vars=["spend"], inputs=None, graph=dummy_graph
    )

    tracker.client.log_param.assert_not_called()


@patch("hamilton.plugins.h_mlflow.mlflow")
def test_mlflow_tracker_status_success(mock_mlflow):
    tracker = MLFlowTracker(experiment_name="test")
    tracker.client = MagicMock()
    tracker.run_id = "1"

    tracker.run_after_graph_execution(success=True)

    tracker.client.set_terminated.assert_called_once_with("1", status="FINISHED")
    mock_mlflow.end_run.assert_called_once_with(status="FINISHED")


@patch("hamilton.plugins.h_mlflow.mlflow")
def test_mlflow_tracker_status_failure(mock_mlflow):
    tracker = MLFlowTracker(experiment_name="test")
    tracker.client = MagicMock()
    tracker.run_id = "1"

    tracker.run_after_graph_execution(success=False)

    tracker.client.set_terminated.assert_called_once_with("1", status="FAILED")
    mock_mlflow.end_run.assert_called_once_with(status="FAILED")
