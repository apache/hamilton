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

from hamilton import ad_hoc_utils, graph, node
from hamilton.execution import grouping
from hamilton.execution.grouping import (
    GroupByRepeatableBlocks,
    GroupNodesAllAsOne,
    GroupNodesByLevel,
    GroupNodesIndividually,
    NodeGroupPurpose,
)
from hamilton.graph import FunctionGraph
from hamilton.lifecycle import base as lifecycle_base
from hamilton.node import NodeType

from tests.resources.dynamic_parallelism import no_parallel, parallel_complex, parallel_linear_basic


def test_group_individually():
    fn_graph = FunctionGraph.from_modules(no_parallel, config={})
    node_grouper = GroupNodesIndividually()
    nodes_grouped = node_grouper.group_nodes(list(fn_graph.nodes.values()))
    assert len(nodes_grouped) == len(fn_graph.nodes)


def test_group_all_as_one():
    fn_graph = FunctionGraph.from_modules(no_parallel, config={})
    node_grouper = GroupNodesAllAsOne()
    nodes_grouped = node_grouper.group_nodes(list(fn_graph.nodes.values()))
    assert len(nodes_grouped) == 1


def test_group_by_level():
    # No good reason you'd ever really want to group this way, but this helps test the grouping
    # system
    fn_graph = FunctionGraph.from_modules(no_parallel, config={})
    node_grouper = GroupNodesByLevel()
    nodes_grouped = node_grouper.group_nodes(list(fn_graph.nodes.values()))
    assert len(nodes_grouped) == 6  # Two are in the same group


def test_group_nodes_by_repeatable_blocks():
    fn_graph = FunctionGraph.from_modules(parallel_linear_basic, config={})
    node_grouper = GroupByRepeatableBlocks()
    nodes_grouped_by_name = {
        group.base_id: group for group in node_grouper.group_nodes(list(fn_graph.nodes.values()))
    }
    assert len(nodes_grouped_by_name["collect-steps"].nodes) == 1
    assert len(nodes_grouped_by_name["expand-steps"].nodes) == 1
    assert len(nodes_grouped_by_name["block-steps"].nodes) == 3
    assert len(nodes_grouped_by_name["number_of_steps"].nodes) == 1
    assert len(nodes_grouped_by_name["final"].nodes) == 1
    assert nodes_grouped_by_name["final"].purpose == NodeGroupPurpose.EXECUTE_SINGLE
    assert nodes_grouped_by_name["number_of_steps"].purpose == NodeGroupPurpose.EXECUTE_SINGLE
    assert nodes_grouped_by_name["block-steps"].purpose == NodeGroupPurpose.EXECUTE_BLOCK
    assert nodes_grouped_by_name["collect-steps"].purpose == NodeGroupPurpose.GATHER
    assert nodes_grouped_by_name["block-steps"].spawning_task_base_id == "expand-steps"
    assert nodes_grouped_by_name["collect-steps"].spawning_task_base_id == "expand-steps"


def test_group_nodes_by_repeatable_blocks_complex():
    fn_graph = FunctionGraph.from_modules(parallel_complex, config={})
    node_grouper = GroupByRepeatableBlocks()
    nodes_grouped_by_name = {
        group.base_id: group for group in node_grouper.group_nodes(list(fn_graph.nodes.values()))
    }
    assert len(nodes_grouped_by_name["collect-steps"].nodes) == 1
    assert len(nodes_grouped_by_name["expand-steps"].nodes) == 1
    assert len(nodes_grouped_by_name["block-steps"].nodes) == 5
    # See comments in parallel_complex.py for why this is -- between start/end of parallelizable block
    assert nodes_grouped_by_name["number_of_steps"].purpose == NodeGroupPurpose.EXECUTE_SINGLE
    assert nodes_grouped_by_name["block-steps"].purpose == NodeGroupPurpose.EXECUTE_BLOCK
    assert nodes_grouped_by_name["collect-steps"].purpose == NodeGroupPurpose.GATHER
    assert nodes_grouped_by_name["block-steps"].spawning_task_base_id == "expand-steps"
    assert nodes_grouped_by_name["collect-steps"].spawning_task_base_id == "expand-steps"


def test_create_task_plan():
    fn_graph = FunctionGraph.from_modules(parallel_linear_basic, config={})
    node_grouper = GroupByRepeatableBlocks()
    nodes_grouped = node_grouper.group_nodes(list(fn_graph.nodes.values()))
    task_plan = grouping.create_task_plan(
        nodes_grouped, ["final"], {}, lifecycle_base.LifecycleAdapterSet()
    )
    assert len(task_plan) == 5
    task_plan_by_id = {task.base_id: task for task in task_plan}
    assert {key: value.base_dependencies for key, value in task_plan_by_id.items()} == {
        "expand-steps": ["number_of_steps"],
        "block-steps": ["expand-steps"],
        "collect-steps": ["block-steps"],
        "final": ["collect-steps"],
        "number_of_steps": [],
    }


def test_task_get_input_vars_not_user_defined():
    def bar(foo: int) -> int:
        return foo + 1

    # This is hacking around function graph which is messy as it is built of larger components
    # (modules), and should instead be broken into smaller pieces (functions/nodes), and have utilities
    # to create it from those.
    fn_graph = graph.create_function_graph(ad_hoc_utils.create_temporary_module(bar), config={})
    node_ = fn_graph["bar"]
    task = grouping.TaskSpec(
        base_id="bar",
        nodes=[node_],
        purpose=NodeGroupPurpose.EXECUTE_SINGLE,
        outputs_to_compute=["bar"],
        overrides={},
        adapter=lifecycle_base.LifecycleAdapterSet(),
        base_dependencies=[],
        spawning_task_base_id=None,
    )
    assert task.get_input_vars() == (["foo"], [])


def test_task_get_input_vars_with_optional():
    def bar(foo: int, baz: int = 1) -> int:
        return foo + 1

    # This is hacking around function graph which is messy as it is built of larger components
    # (modules), and should instead be broken into smaller pieces (functions/nodes), and have utilities
    # to create it from those.
    fn_graph = graph.create_function_graph(ad_hoc_utils.create_temporary_module(bar), config={})
    node_ = fn_graph["bar"]
    task = grouping.TaskSpec(
        base_id="bar",
        nodes=[node_],
        purpose=NodeGroupPurpose.EXECUTE_SINGLE,
        outputs_to_compute=["bar"],
        overrides={},
        adapter=lifecycle_base.LifecycleAdapterSet(),
        base_dependencies=[],
        spawning_task_base_id=None,
    )
    assert task.get_input_vars() == (["foo"], ["baz"])


def test_task_get_input_vars_user_defined():
    node_ = node.Node(name="foo", typ=int, node_source=NodeType.EXTERNAL)
    task = grouping.TaskSpec(
        base_id="foo",
        nodes=[node_],
        purpose=NodeGroupPurpose.EXECUTE_SINGLE,
        outputs_to_compute=["foo"],
        overrides={},
        adapter=lifecycle_base.LifecycleAdapterSet(),
        base_dependencies=[],
        spawning_task_base_id=None,
    )
    assert task.get_input_vars() == (["foo"], [])
