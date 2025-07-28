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

import hamilton.node
from hamilton.caching import fingerprinting
from hamilton.caching.adapter import (
    CachingBehavior,
    CachingEventType,
    HamiltonCacheAdapter,
)
from hamilton.function_modifiers.metadata import cache as cache_decorator
from hamilton.graph import FunctionGraph


@pytest.fixture
def cache_adapter(tmp_path):
    def foo() -> str:
        return "hello-world"

    run_id = "my-run-id"
    adapter = HamiltonCacheAdapter(path=tmp_path)
    adapter.metadata_store.initialize(run_id)
    adapter._fn_graphs[run_id] = FunctionGraph(
        nodes={"foo": hamilton.node.Node.from_fn(foo)},
        config={},
    )
    adapter.behaviors = {run_id: {"foo": CachingBehavior.DEFAULT}}
    adapter._data_savers = {run_id: []}
    adapter._data_loaders = {run_id: []}
    adapter.run_ids.append(run_id)
    adapter.data_versions = {run_id: {}}
    adapter.code_versions = {run_id: {"foo": "0", "bar": "0"}}
    adapter.cache_keys = {run_id: {}}
    adapter._logs = {run_id: []}

    yield adapter

    adapter.metadata_store.delete_all()


def test_post_node_execute_set_result(cache_adapter):
    """Adapter should write to cache and repository if it needs to compute the value"""
    node_name = "foo"
    result = 123
    data_version = fingerprinting.hash_value(result)
    run_id = cache_adapter.last_run_id

    assert cache_adapter.data_versions.get(node_name) is None
    assert cache_adapter.result_store.exists(data_version) is False

    cache_adapter.data_versions[run_id][node_name] = data_version
    cache_adapter.post_node_execute(
        run_id=run_id,  # latest run_id
        node_=cache_adapter._fn_graphs[run_id].nodes[node_name],
        kwargs={},
        result=result,
    )

    assert cache_adapter.result_store.exists(data_version)
    assert cache_adapter.result_store.get(data_version=data_version) == result


def test_do_execute_reads_data_version_directly_from_memory(cache_adapter):
    """Adapter shouldn't check the repository if fingerprint is available"""

    def foo() -> int:
        return 123

    cached_result = foo()
    data_version = fingerprinting.hash_value(cached_result)
    run_id = cache_adapter.last_run_id

    cache_adapter.data_versions[run_id]["foo"] = data_version
    cache_adapter.pre_node_execute(run_id=run_id, node_=hamilton.node.Node.from_fn(foo), kwargs={})

    assert not any(
        event.event_type == CachingEventType.GET_DATA_VERSION and event.actor == "metadata_store"
        for event in cache_adapter.logs(run_id)
    )


def test_run_to_execute_repo_cache_desync(cache_adapter):
    """The adapter determines the value is in cache,
    but there's an error loading the value from cache.

    The adapter should delete metadata store keys to force recompute and
    writing the result to cache

    NOTE that this will only log and error and not raise any Exception.
    This is because adapters cannot currently raise Exception that stop
    the main execution.
    """

    def foo() -> int:
        return 123

    run_id = cache_adapter.last_run_id  # latest run_id

    # set data version in memory
    cache_adapter.data_versions[run_id]["foo"] = fingerprinting.hash_value(foo())
    cache_adapter.do_node_execute(run_id=run_id, node_=hamilton.node.Node.from_fn(foo), kwargs={})

    # found data version in memory, but the value wasn't in cache
    # forcing deletion from metadata_store and recompute
    logs = cache_adapter.logs(run_id, level="debug")
    assert any(event.event_type == CachingEventType.MISSING_RESULT for event in logs["foo"])
    assert any(event.event_type == CachingEventType.EXECUTE_NODE for event in logs["foo"])


@pytest.mark.parametrize(
    "behavior",
    [
        "default",
        "recompute",
        "disable",
        "ignore",
    ],
)
def test_cache_tag_resolved(cache_adapter, behavior):
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes["foo"]
    node._tags = {cache_decorator.BEHAVIOR_KEY: behavior}
    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(node)
    assert resolved_behavior == CachingBehavior.from_string(behavior)


def test_default_behavior(cache_adapter):
    h_node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes["foo"]
    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(h_node)
    assert resolved_behavior == CachingBehavior.DEFAULT


def test_driver_behavior_overrides_cache_tag(cache_adapter):
    node_name = "foo"
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes[node_name]
    node._tags = {cache_decorator.BEHAVIOR_KEY: "recompute"}

    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(node=node, disable=[node_name])

    assert resolved_behavior == CachingBehavior.DISABLE


def test_raise_if_multiple_driver_behavior_for_same_node(cache_adapter):
    node_name = "foo"
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes[node_name]

    with pytest.raises(ValueError):
        HamiltonCacheAdapter._resolve_node_behavior(
            node,
            disable=[node_name],
            recompute=[node_name],
        )
