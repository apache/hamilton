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

"""A dataflow that already contains a node named ``_result_builder``.

``graph_utils.find_functions`` filters out ``_``-prefixed *functions*, which is why the tracker's
synthetic node is named this way. An external input takes its name from a parameter, and
parameters are never filtered, so the name is reachable after all. Decorator-generated names
(``@extract_columns("_result_builder")``) bypass the filter the same way.
"""


def uses_the_reserved_name(_result_builder: int) -> int:
    return _result_builder + 1
