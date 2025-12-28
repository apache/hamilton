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

from typing import Optional

from hamilton.graph_types import HamiltonNode
from hamilton.lifecycle import api


class MyTagValidator(api.StaticValidator):
    def run_to_validate_node(
        self, *, node: HamiltonNode, **future_kwargs
    ) -> tuple[bool, Optional[str]]:
        if node.tags.get("node_type", "") == "output":
            table_name = node.tags.get("table_name")
            if not table_name:  # None or empty
                error_msg = f"Node {node.tags['module']}.{node.name} is an output node, but does not have a table_name tag."
                return False, error_msg
        return True, None


if __name__ == "__main__":
    import good_module

    from hamilton import driver

    tag_validator = MyTagValidator()
    dr = driver.Builder().with_modules(good_module).with_adapters(tag_validator).build()
    print(dr.execute([good_module.foo]))

    import bad_module

    # this should error
    dr = driver.Builder().with_modules(bad_module).with_adapters(tag_validator).build()
