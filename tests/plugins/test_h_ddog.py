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

pytest.importorskip("ddtrace")

from hamilton.plugins.h_ddog import AsyncDDOGTracer, DDOGTracer


@pytest.fixture()
def mock_tracer():
    with patch("hamilton.plugins.h_ddog.tracer") as t:
        mock_span = MagicMock()
        mock_span.context = MagicMock(trace_id=1, span_id=2)
        mock_span.__exit__ = MagicMock(return_value=False)
        t.start_span.return_value = mock_span
        t.current_trace_context.return_value = None
        yield t


class TestDDOGTracerLifecycle:
    def test_span_lifecycle(self, mock_tracer):
        tracer_inst = DDOGTracer(root_name="test-root", service="test-svc")
        run_id = "run-1"

        tracer_inst.run_before_graph_execution(run_id=run_id)
        assert mock_tracer.start_span.call_count == 1

        tracer_inst.run_before_node_execution(
            node_name="node_a",
            node_kwargs={},
            node_tags={"module": "test"},
            task_id=None,
            run_id=run_id,
        )
        assert mock_tracer.start_span.call_count == 2

        tracer_inst.run_after_node_execution(
            node_name="node_a", error=None, task_id=None, run_id=run_id
        )
        node_span = mock_tracer.start_span.return_value
        node_span.__exit__.assert_called_with(None, None, None)

        tracer_inst.run_after_graph_execution(error=None, run_id=run_id)

    def test_span_lifecycle_with_error(self, mock_tracer):
        tracer_inst = DDOGTracer(root_name="test-root")
        run_id = "run-err"

        tracer_inst.run_before_graph_execution(run_id=run_id)
        tracer_inst.run_before_node_execution(
            node_name="node_b",
            node_kwargs={},
            node_tags={},
            task_id=None,
            run_id=run_id,
        )

        err = ValueError("boom")
        tracer_inst.run_after_node_execution(
            node_name="node_b", error=err, task_id=None, run_id=run_id
        )
        node_span = mock_tracer.start_span.return_value
        node_span.__exit__.assert_called_with(ValueError, err, err.__traceback__)

        tracer_inst.run_after_graph_execution(error=err, run_id=run_id)

    def test_task_span_lifecycle(self, mock_tracer):
        tracer_inst = DDOGTracer(root_name="test-root")
        run_id = "run-task"

        tracer_inst.run_before_graph_execution(run_id=run_id)
        tracer_inst.run_before_task_execution(task_id="task-1", run_id=run_id)
        tracer_inst.run_before_node_execution(
            node_name="node_c",
            node_kwargs={},
            node_tags={},
            task_id="task-1",
            run_id=run_id,
        )
        tracer_inst.run_after_node_execution(
            node_name="node_c", error=None, task_id="task-1", run_id=run_id
        )
        tracer_inst.run_after_task_execution(task_id="task-1", run_id=run_id, error=None)
        tracer_inst.run_after_graph_execution(error=None, run_id=run_id)


class TestAsyncDDOGTracer:
    def test_instantiation(self):
        inst = AsyncDDOGTracer(root_name="async-root", service="async-svc")
        assert inst._impl.root_name == "async-root"
        assert inst._impl.service == "async-svc"

    def test_instantiation_with_causal_links(self):
        inst = AsyncDDOGTracer(root_name="async-root", include_causal_links=True, service=None)
        assert inst._impl.include_causal_links is True


class TestSerialization:
    def test_getstate_setstate_round_trip(self, mock_tracer):
        tracer_inst = DDOGTracer(root_name="ser-root", service="ser-svc")
        run_id = "run-ser"

        tracer_inst.run_before_graph_execution(run_id=run_id)

        state = tracer_inst._impl.__getstate__()
        assert "root_trace_name" in state
        assert state["root_trace_name"] == "ser-root"
        assert state["service"] == "ser-svc"

        new_impl = object.__new__(type(tracer_inst._impl))
        new_impl.__setstate__(state)
        assert new_impl.root_name == "ser-root"
        assert new_impl.service == "ser-svc"
        assert new_impl.include_causal_links is False
        assert isinstance(new_impl.run_span_cache, dict)

        tracer_inst.run_after_graph_execution(error=None, run_id=run_id)

    def test_serialize_deserialize_span_dict(self, mock_tracer):
        from ddtrace.trace import Context, Span

        from hamilton.plugins.h_ddog import _DDOGTracerImpl

        mock_span = MagicMock(spec=Span)
        mock_span.context = MagicMock(trace_id=123, span_id=456)
        span_dict = {"key1": mock_span}

        serialized = _DDOGTracerImpl._serialize_span_dict(span_dict)
        assert serialized["key1"]["trace_id"] == 123
        assert serialized["key1"]["span_id"] == 456

        deserialized = _DDOGTracerImpl._deserialize_span_dict(serialized)
        assert "key1" in deserialized
        assert isinstance(deserialized["key1"], Context)
