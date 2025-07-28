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

from concurrent.futures import Future
from typing import Any

from hamilton import lifecycle
from hamilton.plugins.h_threadpool import FutureAdapter, _new_fn


def test_new_fn_with_no_futures():
    def sample_fn(a, b):
        return a + b

    result = _new_fn(sample_fn, a=1, b=2)
    assert result == 3


def test_new_fn_with_futures():
    def sample_fn(a, b):
        return a + b

    future_a = Future()
    future_b = Future()
    future_a.set_result(1)
    future_b.set_result(2)

    result = _new_fn(sample_fn, a=future_a, b=future_b)
    assert result == 3


def test_future_adapter_do_remote_execute():
    def sample_fn(a, b):
        return a + b

    adapter = FutureAdapter(max_workers=2)
    future = adapter.do_remote_execute(execute_lifecycle_for_node=sample_fn, node=None, a=1, b=2)
    assert future.result() == 3


def test_future_adapter_do_remote_execute_with_futures():
    def sample_fn(a, b):
        return a + b

    future_a = Future()
    future_b = Future()
    future_a.set_result(1)
    future_b.set_result(2)

    adapter = FutureAdapter(max_workers=2)
    future = adapter.do_remote_execute(
        execute_lifecycle_for_node=sample_fn, node=None, a=future_a, b=future_b
    )
    assert future.result() == 3


def test_future_adapter_build_result():
    adapter = FutureAdapter(max_workers=2)
    future_a = Future()
    future_b = Future()
    future_a.set_result(1)
    future_b.set_result(2)

    result = adapter.build_result(a=future_a, b=future_b)
    assert result == {"a": 1, "b": 2}


def test_future_adapter_input_types():
    adapter = FutureAdapter()
    assert adapter.input_types() == [Any]


def test_future_adapter_output_type():
    adapter = FutureAdapter()
    assert adapter.output_type() == Any


def test_future_adapter_input_types_with_result_builder():
    """Tests that we ignore exposing the input types of the wrapped result builder."""

    class MockResultBuilder(lifecycle.ResultBuilder):
        def build_result(self, **outputs: Any) -> Any:
            pass

        def input_types(self):
            return [int, str]

    adapter = FutureAdapter(result_builder=MockResultBuilder())
    assert adapter.input_types() == [Any]


def test_future_adapter_output_type_with_result_builder():
    class MockResultBuilder(lifecycle.ResultBuilder):
        def build_result(self, **outputs: Any) -> Any:
            pass

        def output_type(self):
            return dict

    adapter = FutureAdapter(result_builder=MockResultBuilder())
    assert adapter.output_type() == dict


def test_future_adapter_build_result_with_result_builder():
    class MockResultBuilder(lifecycle.ResultBuilder):
        def build_result(self, **outputs):
            return sum(outputs.values())

        def input_types(self):
            return [int]

        def output_type(self):
            return int

    adapter = FutureAdapter(result_builder=MockResultBuilder())
    future_a = Future()
    future_b = Future()
    future_a.set_result(1)
    future_b.set_result(2)

    result = adapter.build_result(a=future_a, b=future_b)
    assert result == 3
