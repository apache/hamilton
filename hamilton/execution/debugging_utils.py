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

from typing import List

from hamilton.execution.grouping import NodeGroup, NodeGroupPurpose, TaskSpec

"""A set of utilities for debugging/printing out data"""
group_purpose_icons = {
    NodeGroupPurpose.EXPAND_UNORDERED: "⫳",
    NodeGroupPurpose.GATHER: "⋃",
    NodeGroupPurpose.EXECUTE_BLOCK: "᠅",
    NodeGroupPurpose.EXECUTE_SINGLE: "•",
}


def print_node_groups(node_groups: List[NodeGroup]):
    """Prints out the node groups in a clean, tree-like format.

    :param node_groups:
    :return:
    """
    for group in node_groups:
        node_icon = group_purpose_icons[group.purpose]
        print(f"{node_icon} {group.base_id}")
        for node_ in group.nodes:
            print(f"   • {node_.name} [ƒ({','.join(map(lambda n: n.name, node_.dependencies))})]")


def print_tasks(tasks: List[TaskSpec]):
    """Prints out the node groups in a clean, tree-like format.

    :param tasks:
    :return:
    """
    print()
    for task in tasks:
        node_icon = group_purpose_icons[task.purpose]
        print(f"{node_icon} {task.base_id} [ƒ({', '.join(task.base_dependencies)})]")
        for node_ in task.nodes:
            print(
                f"   • {node_.name}"
            )  # ƒ({', '.join(map(lambda n: n.name, node_.dependencies))})")
