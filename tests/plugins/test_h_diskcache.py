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

import inspect
import pathlib

import pytest

from hamilton import ad_hoc_utils, driver, graph_types, node
from hamilton.plugins import h_diskcache


def _callable_to_node(callable) -> node.Node:
    return node.Node(
        name=callable.__name__,
        typ=inspect.signature(callable).return_annotation,
        callabl=callable,
    )


@pytest.fixture()
def hook(tmp_path: pathlib.Path):
    return h_diskcache.DiskCacheAdapter(cache_path=str(tmp_path.resolve()))


@pytest.fixture()
def node_a():
    """Default function implementation"""

    def A(external_input: int) -> int:
        return external_input % 7

    return _callable_to_node(A)


@pytest.fixture()
def node_a_body():
    """The function A() has modulo 5 instead of 7"""

    def A(external_input: int) -> int:
        return external_input % 5

    return _callable_to_node(A)


@pytest.fixture()
def node_a_docstring():
    """The function A() has a docstring"""

    def A(external_input: int) -> int:
        """This one has a docstring"""
        return external_input % 7

    return _callable_to_node(A)


def test_set_result(hook: h_diskcache.DiskCacheAdapter, node_a: node.Node):
    """Hook sets value and assert value in cache"""
    node_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_kwargs = dict(external_input=7)
    cache_key = (node_hash, *node_kwargs.values())
    result = 2

    hook.cache_vars = [node_a.name]
    # used_nodes_hash would be set by run_to_execute() hook
    hook.used_nodes_hash[node_a.name] = node_hash
    hook.run_after_node_execution(
        node_name=node_a.name,
        node_kwargs=node_kwargs,
        result=result,
    )

    # run_to_execute_node() hook would get cache
    assert hook.cache.get(key=cache_key) == result


def test_get_result(hook: h_diskcache.DiskCacheAdapter, node_a: node.Node):
    """Hooks get value and assert cache hit"""
    node_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_kwargs = dict(external_input=7)
    result = 2
    cache_key = (node_hash, *node_kwargs.values())

    hook.cache_vars = [node_a.name]
    # run_after_node_execution() would set cache
    hook.cache.set(key=cache_key, value=result)
    hook.cache.stats(enable=True, reset=True)
    hook.run_to_execute_node(
        node_name=node_a.name,
        node_kwargs=node_kwargs,
        node_callable=node_a.callable,
    )

    # 1 hit, 0 miss
    assert hook.cache.stats() == (1, 0)


def test_append_nodes_history(
    hook: h_diskcache.DiskCacheAdapter,
    node_a: node.Node,
    node_a_body: node.Node,
):
    """Assert the CacheHook.nodes_history is growing;
    doesn't check for commit to cache
    """
    node_name = "A"
    node_kwargs = dict(external_input=7)
    hook.cache_vars = [node_a.name]

    # node version 1
    hook.used_nodes_hash[node_name] = graph_types.hash_source_code(node_a.callable, strip=True)
    hook.run_to_execute_node(
        node_name=node_name,
        node_kwargs=node_kwargs,
        node_callable=node_a.callable,
    )

    # check history
    assert len(hook.nodes_history.get(node_name, [])) == 1

    # node version 2
    hook.used_nodes_hash[node_name] = graph_types.hash_source_code(node_a_body.callable, strip=True)
    hook.run_to_execute_node(
        node_name=node_name,
        node_kwargs=node_kwargs,
        node_callable=node_a_body.callable,
    )

    assert len(hook.nodes_history.get(node_name, [])) == 2


def test_commit_nodes_history(hook: h_diskcache.DiskCacheAdapter):
    """Commit node history to cache"""
    hook.nodes_history = dict(A=["hash_1", "hash_2"])

    hook.run_after_graph_execution()

    assert hook.cache.get(h_diskcache.DiskCacheAdapter.nodes_history_key) == hook.nodes_history


def test_evict_all_except(
    hook: h_diskcache.DiskCacheAdapter,
    node_a: node.Node,
    node_a_body: node.Node,
):
    """Check utility function to evict all except passed nodes"""
    node_a_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_a_body_hash = graph_types.hash_source_code(node_a_body.callable, strip=True)
    hook.cache[h_diskcache.DiskCacheAdapter.nodes_history_key] = dict(
        A=[node_a_hash, node_a_body_hash]
    )

    eviction_counter = h_diskcache.evict_all_except(nodes_to_keep=dict(A=node_a), cache=hook.cache)

    assert eviction_counter == 1
    assert hook.cache[h_diskcache.DiskCacheAdapter.nodes_history_key] == dict(A=[node_a_hash])


def test_evict_from_driver(
    hook: h_diskcache.DiskCacheAdapter,
    node_a: node.Node,
    node_a_body: node.Node,
):
    """Check utility function to evict all except driver"""
    node_a_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_a_body_hash = graph_types.hash_source_code(node_a_body.callable, strip=True)
    hook.cache[h_diskcache.DiskCacheAdapter.nodes_history_key] = dict(
        A=[node_a_hash, node_a_body_hash]
    )
    module = ad_hoc_utils.create_temporary_module(node_a.callable)
    dr = driver.Builder().with_modules(module).with_adapters(hook).build()

    output = h_diskcache.evict_all_except_driver(dr)

    assert output["eviction_counter"] == 1
    assert hook.cache[h_diskcache.DiskCacheAdapter.nodes_history_key] == dict(A=[node_a_hash])
