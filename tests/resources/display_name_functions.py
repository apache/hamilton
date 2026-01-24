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

"""Test module for display_name tag support in graphviz visualization.

See: https://github.com/apache/hamilton/issues/1413
"""

from hamilton.function_modifiers import tag


def input_a() -> int:
    """A simple input node without display_name."""
    return 1


@tag(display_name="My Custom Display Name")
def node_with_display_name(input_a: int) -> int:
    """A node with a custom display name for visualization."""
    return input_a + 1


@tag(display_name='Special <Characters> & "Quotes"')
def node_with_special_chars(input_a: int) -> int:
    """A node with special HTML characters that need escaping."""
    return input_a * 2


@tag(owner="data-science")
def node_without_display_name(input_a: int) -> int:
    """A node with other tags but no display_name."""
    return input_a + 10


@tag(display_name="Final Output Node", owner="analytics")
def output_node(node_with_display_name: int, node_without_display_name: int) -> int:
    """A node with display_name and other tags."""
    return node_with_display_name + node_without_display_name
