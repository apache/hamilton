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

import json

from hamilton import driver, graph_types

from tests.resources.dynamic_parallelism import no_parallel

# `version` value isn't hardcoded because it's Python version-dependent
EXPECTED_JSON = {
    "nodes": [
        {
            "name": "final",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["sum_step_squared_plus_step_cubed"],
            "optional_dependencies": [],
            "source": 'def final(sum_step_squared_plus_step_cubed: int) -> int:\n    print("finalizing")\n    return sum_step_squared_plus_step_cubed\n',
            "documentation": "",
            "version": "27af6c2870dd4ca92335df4a9ff6c84da829d792a4c9f690f2f57193dbf3395a",
        },
        {
            "name": "number_of_steps",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": [],
            "optional_dependencies": [],
            "source": "def number_of_steps() -> int:\n    return 5\n",
            "documentation": "",
            "version": "48945782868c44bca1b159682d48bee3a1c1e9be73cf059c5087d0d3258fdc78",
        },
        {
            "name": "step_cubed",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["steps"],
            "optional_dependencies": [],
            "source": 'def step_cubed(steps: int) -> int:\n    print("cubing step {}".format(steps))\n    return steps**3\n',
            "documentation": "",
            "version": "f82b894f3d8a8de9cf798a41e08c1f38c8396e86c569cb73b7d78b4420f9dd99",
        },
        {
            "name": "step_squared",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["steps"],
            "optional_dependencies": [],
            "source": 'def step_squared(steps: int) -> int:\n    print("squaring step {}".format(steps))\n    return steps**2\n',
            "documentation": "",
            "version": "371bff5e02e091314e0ef2c3ca3003a496a119f9164d3e1827fe64d5f8c4aaba",
        },
        {
            "name": "step_squared_plus_step_cubed",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["step_cubed", "step_squared"],
            "optional_dependencies": [],
            "source": 'def step_squared_plus_step_cubed(step_squared: int, step_cubed: int) -> int:\n    print("adding step squared and step cubed")\n    return step_squared + step_cubed\n',
            "documentation": "",
            "version": "fe76eaaf43a6b79a706574ea6a8f00fe5b6439e3b8d7ceb879ab938b7722a1b3",
        },
        {
            "name": "steps",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["number_of_steps"],
            "optional_dependencies": [],
            "source": "def steps(number_of_steps: int) -> int:\n    return number_of_steps\n",
            "documentation": "",
            "version": "111ccfe2b5e8754e5ada1dae3ffc49d27b450a98e3be61f9308144aa5a444921",
        },
        {
            "name": "sum_step_squared_plus_step_cubed",
            "tags": {"module": "tests.resources.dynamic_parallelism.no_parallel"},
            "output_type": "int",
            "required_dependencies": ["step_squared_plus_step_cubed"],
            "optional_dependencies": [],
            "source": 'def sum_step_squared_plus_step_cubed(step_squared_plus_step_cubed: int) -> int:\n    print("summing step squared")\n    return step_squared_plus_step_cubed\n',
            "documentation": "",
            "version": "7831c9ed5f45e0b8ce3de34c3a5e2b4d4467b1ebc44cb55ea6ecae8f7dbf749d",
        },
    ]
}


def test_export_execution():
    dr = driver.Builder().with_modules(no_parallel).build()
    graph = graph_types.HamiltonGraph.from_graph(dr.graph)

    # can't hard code HamiltonNode.version because it depends on Python version
    for n in graph.nodes:
        for json_n in EXPECTED_JSON["nodes"]:
            if json_n["name"] == n.name:
                json_n["version"] = n.version

    json_str = dr.export_execution(["final"])
    assert json_str == json.dumps(EXPECTED_JSON)
