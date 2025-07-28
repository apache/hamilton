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

import functools
import pathlib
import shelve

import pytest

from hamilton import graph_types, node
from hamilton.lifecycle.default import CacheAdapter


def _callable_to_node(callable, name=None) -> node.Node:
    return node.Node.from_fn(callable, name)


@pytest.fixture()
def hook(tmp_path: pathlib.Path):
    return CacheAdapter(cache_path=str((tmp_path / "cache.db").resolve()))


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


@pytest.fixture()
def node_a_partial():
    """The function A() is a partial"""

    def A(external_input: int, remainder: int) -> int:
        return external_input % remainder

    base_node: node.Node = _callable_to_node(A)

    A = functools.partial(A, remainder=7)
    base_node._callable = A
    del base_node.input_types["remainder"]
    return base_node


@pytest.fixture()
def node_a_nested_partial():
    """The function A() is a partial"""

    def A(external_input: int, remainder: int, extra: int) -> int:
        return external_input % remainder

    base_node: node.Node = _callable_to_node(A)
    A = functools.partial(A, remainder=7)
    A = functools.partial(A, extra=7)
    base_node._callable = A
    del base_node.input_types["remainder"]
    del base_node.input_types["extra"]
    return base_node


def test_set_result(hook: CacheAdapter, node_a: node.Node):
    """Hook sets value and assert value in cache"""
    node_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_kwargs = dict(external_input=7)
    cache_key = CacheAdapter.create_key(node_hash, node_kwargs)
    result = 2

    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
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


def test_get_result(hook: CacheAdapter, node_a: node.Node):
    """Hooks get value and assert cache hit"""
    node_hash = graph_types.hash_source_code(node_a.callable, strip=True)
    node_kwargs = dict(external_input=7)
    result = 2
    cache_key = CacheAdapter.create_key(node_hash, node_kwargs)

    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
    hook.cache_vars = [node_a.name]
    # run_after_node_execution() would set cache
    hook.cache[cache_key] = result
    retrieved = hook.run_to_execute_node(
        node_name=node_a.name,
        node_kwargs=node_kwargs,
        node_callable=node_a.callable,
    )

    assert retrieved == result


def test_append_nodes_history(
    hook: CacheAdapter,
    node_a: node.Node,
    node_a_body: node.Node,
):
    """Assert the CacheHook.nodes_history is growing;
    doesn't check for commit to cache
    """
    node_name = "A"
    node_kwargs = dict(external_input=7)
    hook.cache_vars = [node_a.name]

    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
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


def test_commit_nodes_history(hook: CacheAdapter):
    """Commit node history to cache"""
    hook.nodes_history = dict(A=["hash_1", "hash_2"])

    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
    hook.run_after_graph_execution()

    # need to reopen the hook cache
    with shelve.open(hook.cache_path) as cache:
        assert cache.get(CacheAdapter.nodes_history_key) == hook.nodes_history


def test_partial_handling(hook: CacheAdapter, node_a_partial: node.Node):
    """Tests partial functions are handled properly"""
    hook.cache_vars = [node_a_partial.name]
    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
    node_kwargs = dict(external_input=7)
    result = hook.run_to_execute_node(
        node_name=node_a_partial.name,
        node_kwargs=node_kwargs,
        node_callable=node_a_partial.callable,
    )
    hook.run_after_node_execution(
        node_name=node_a_partial.name,
        node_kwargs=node_kwargs,
        result=result,
    )
    result2 = hook.run_to_execute_node(
        node_name=node_a_partial.name,
        node_kwargs=node_kwargs,
        node_callable=node_a_partial.callable,
    )
    assert result2 == result


def test_nested_partial_handling(hook: CacheAdapter, node_a_nested_partial: node.Node):
    """Tests nested partial functions are handled properly"""
    hook.cache_vars = [node_a_nested_partial.name]
    hook.run_before_graph_execution(graph=graph_types.HamiltonGraph([]))  # needed to open cache
    node_kwargs = dict(external_input=7)
    result = hook.run_to_execute_node(
        node_name=node_a_nested_partial.name,
        node_kwargs=node_kwargs,
        node_callable=node_a_nested_partial.callable,
    )
    hook.run_after_node_execution(
        node_name=node_a_nested_partial.name,
        node_kwargs=node_kwargs,
        result=result,
    )
    result2 = hook.run_to_execute_node(
        node_name=node_a_nested_partial.name,
        node_kwargs=node_kwargs,
        node_callable=node_a_nested_partial.callable,
    )
    assert result2 == result
