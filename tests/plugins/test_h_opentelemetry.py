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

from unittest import mock

import pytest

pytest.importorskip("opentelemetry.sdk")

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from hamilton import ad_hoc_utils, driver, graph_types
from hamilton.plugins import h_opentelemetry


def a(x: int) -> int:
    return x + 1


def b(a: int) -> int:
    return a * 2


def c(a: int, b: int) -> int:
    return a + b


def _traced_driver(exporter: InMemorySpanExporter) -> driver.Driver:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    tracer = h_opentelemetry.OpenTelemetryTracer(tracer=provider.get_tracer(__name__))
    # a fresh module per driver, so no source hash is reused from another test
    module = ad_hoc_utils.create_temporary_module(a, b, c)
    return driver.Builder().with_modules(module).with_adapters(tracer).build()


def test_node_sources_are_hashed_once_across_executions():
    dr = _traced_driver(InMemorySpanExporter())
    with mock.patch.object(
        graph_types, "hash_source_code", wraps=graph_types.hash_source_code
    ) as hash_source_code:
        dr.execute(["c"], inputs={"x": 1})
        first_execution_calls = hash_source_code.call_count
        dr.execute(["c"], inputs={"x": 1})
    # the second execution reuses every hash from the first
    assert hash_source_code.call_count == first_execution_calls
    # one hash per node function: the input `x` shares the hash of `a`, which declares it
    assert first_execution_calls == 3


def test_span_versions_match_source_hashes():
    exporter = InMemorySpanExporter()
    dr = _traced_driver(exporter)
    dr.execute(["c"], inputs={"x": 1})
    dr.execute(["c"], inputs={"x": 1})
    spans = exporter.get_finished_spans()

    graph_versions = [
        s.attributes["graph_version"] for s in spans if "graph_version" in s.attributes
    ]
    assert graph_versions == [graph_types.HamiltonGraph.from_graph(dr.graph).version] * 2

    node_versions = sorted(
        (s.name, s.attributes["node_version"]) for s in spans if "node_version" in s.attributes
    )
    expected = [(fn.__name__, graph_types.hash_source_code(fn, strip=True)) for fn in (a, b, c)]
    assert node_versions == sorted(expected * 2)
