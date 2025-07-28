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
import json
import pathlib

from typer.testing import CliRunner

from hamilton.cli.__main__ import cli

from tests.resources import example_module

runner = CliRunner()


def test_cli_build_success():
    module_path = inspect.getfile(example_module)
    inputs = ["--json-out", "build", module_path]

    result = runner.invoke(cli, inputs)

    assert result.exit_code == 0
    message = json.loads(result.stdout)
    assert message["success"] is True


def test_cli_view_default(tmp_path: pathlib.Path):
    module_path = inspect.getfile(example_module)
    inputs = ["--json-out", "view", module_path]
    # output_file_path = tmp_path / "dag.png"  # default file name

    result = runner.invoke(cli, inputs)

    assert result.exit_code == 0
    message = json.loads(result.stdout)
    assert message["success"] is True
    # TODO difficult to assert the output file path from test
    # assert output_file_path.exists()


# def test_cli_view_output_arg(tmp_path: pathlib.Path):
#     module_path = inspect.getfile(example_module)
#     output_file_path = tmp_path / "other_name.png"
#     inputs = [
#         "view",
#         "--output",
#         str(output_file_path),
#         module_path,
#     ]

#     result = runner.invoke(cli, inputs)
#     message = json.loads(result.stdout)

#     assert result.exit_code == 0
#     assert message["success"] is True
#     assert output_file_path.exists()


def test_cli_version():
    module_path = inspect.getfile(example_module)
    inputs = ["--json-out", "version", module_path]

    result = runner.invoke(cli, inputs)

    assert result.exit_code == 0
    message = json.loads(result.stdout)
    assert message["success"] is True
