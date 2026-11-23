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

import hashlib
import inspect
import logging
from functools import wraps
from pathlib import Path
from types import FunctionType, ModuleType
from unittest.mock import mock_open, patch

from hamilton import driver as hamilton_driver
from hamilton.graph import FunctionGraph
from hamilton_sdk.api.projecttypes import GitInfo
from hamilton_sdk.driver import (
    _extract_node_templates_from_function_graph,
    _get_code_artifact_name,
    _hash_module,
    extract_code_artifacts_from_function_graph,
    hash_dag,
)

from tests.resources import colliding_step_sources, pipe_source_tracking


def test_pipe_step_code_artifacts():
    dr = hamilton_driver.Builder().with_modules(pipe_source_tracking).build()
    assert dr.execute(["input_pipe", "output_pipe", "mutated"], inputs={"value": 1}) == {
        "input_pipe": 4,
        "output_pipe": 3,
        "mutated": 3,
    }
    templates = {
        item["name"]: item for item in _extract_node_templates_from_function_graph(dr.graph)
    }
    repo_base_path = str(Path(pipe_source_tracking.__file__).parent)
    vcs_info = GitInfo(
        "main", "test-commit", True, "https://github.com/apache/hamilton", repo_base_path
    )
    artifacts = extract_code_artifacts_from_function_graph(dr.graph, vcs_info, repo_base_path)

    for node_name, function in {
        "input_pipe.increment": pipe_source_tracking._increment,
        "output_pipe.increment": pipe_source_tracking._increment,
        "mutated.with_mutator": pipe_source_tracking._mutator,
    }.items():
        function_name = _get_code_artifact_name(function)
        assert templates[node_name]["code_artifact_pointers"][0] == function_name
        matching_artifacts = [
            artifact for artifact in artifacts if artifact["name"] == function_name
        ]
        assert len(matching_artifacts) == 1
        artifact = matching_artifacts[0]
        source_lines, start = inspect.getsourcelines(function)
        assert artifact["path"] == "pipe_source_tracking.py"
        assert artifact["start"] == start - 1
        assert artifact["end"] == start - 1 + len(source_lines)

    for name in ["input_pipe", "output_pipe", "mutated"]:
        assert templates[name]["code_artifact_pointers"] == [
            _get_code_artifact_name(getattr(pipe_source_tracking, name))
        ]
    assert len(artifacts) == 5


def test_chained_steps_with_colliding_names_link_to_their_own_source():
    dr = hamilton_driver.Builder().with_modules(colliding_step_sources).build()
    assert dr.execute(["input_chain", "output_chain"], inputs={"value": 1}) == {
        "input_chain": 40,
        "output_chain": 40,
    }
    templates = {
        item["name"]: item for item in _extract_node_templates_from_function_graph(dr.graph)
    }
    repo_base_path = str(Path(colliding_step_sources.__file__).parent)
    vcs_info = GitInfo(
        "main", "test-commit", True, "https://github.com/apache/hamilton", repo_base_path
    )
    artifacts = extract_code_artifacts_from_function_graph(dr.graph, vcs_info, repo_base_path)
    artifacts_by_name = {artifact["name"]: artifact for artifact in artifacts}
    functions = {
        "first": colliding_step_sources._steps[0],
        "second": colliding_step_sources._steps[1],
        "lambda_add": colliding_step_sources._steps[2],
        "lambda_multiply": colliding_step_sources._steps[3],
    }
    # Both pairs collide even when __qualname__ is used without a source location.
    assert functions["first"].__qualname__ == functions["second"].__qualname__
    assert functions["lambda_add"].__qualname__ == functions["lambda_multiply"].__qualname__
    pointers = []
    for step_name, function in functions.items():
        pointer = templates[f"input_chain.{step_name}"]["code_artifact_pointers"][0]
        pointers.append(pointer)
        assert templates[f"output_chain.{step_name}"]["code_artifact_pointers"][0] == pointer
        artifact = artifacts_by_name[pointer]
        source_lines, start = inspect.getsourcelines(function)
        assert artifact["path"] == "colliding_step_sources.py"
        assert artifact["start"] == start - 1
        assert artifact["end"] == start - 1 + len(source_lines)
        assert artifact["url"].endswith(f"/colliding_step_sources.py#L{start}")
    assert len(set(pointers)) == 4
    # Each helper is shared by two chains, but emitted only once.
    assert len(artifacts) == len(artifacts_by_name) == 6


def test_artifact_identity_reuses_factory_source_and_unwraps_decorators():
    original = colliding_step_sources._steps[0]
    recreated = colliding_step_sources._make_step(True)
    assert recreated is not original

    @wraps(original)
    def wrapped(value):
        return original(value)

    assert _get_code_artifact_name(original) == _get_code_artifact_name(recreated)
    assert _get_code_artifact_name(original) == _get_code_artifact_name(wrapped)


def test_artifact_identity_is_stable_when_checkout_moves(tmp_path):
    original = colliding_step_sources._steps[0]
    original_name = _get_code_artifact_name(original)
    moved_file = str(tmp_path / "colliding_step_sources.py")
    moved = FunctionType(original.__code__.replace(co_filename=moved_file), original.__globals__)
    moved.__qualname__ = original.__qualname__
    with patch.object(colliding_step_sources, "__file__", moved_file):
        assert _get_code_artifact_name(moved) == original_name


def test_dag_hash_changes_when_same_named_step_source_changes():
    graph = hamilton_driver.Builder().with_modules(colliding_step_sources).build().graph
    nodes = dict(graph.nodes)
    name = "input_chain.first"
    nodes[name] = nodes[name].copy_with(
        originating_functions=(colliding_step_sources._steps[1],)
        + nodes[name].originating_functions[1:]
    )
    assert hash_dag(FunctionGraph(nodes, config={})) != hash_dag(graph)


@patch("builtins.open", new_callable=mock_open, read_data=b"print('hello world')\n")
def test_hash_module_with_mock(mock_file):
    """Tests that can successfully hash something - this test should be deterministic."""
    module = ModuleType("test_module")
    module.__file__ = "/path/to/test_module.py"
    module.__package__ = "mypackage"
    seen = set()
    # Create a hash object
    h = hashlib.sha256()

    # Generate a hash of the module
    h = _hash_module(module, h, seen)

    # Verify that the hash is correct
    assert h.hexdigest() == "2d543015627a771436b30ea79fd0ecda8df8bcd77b3d55661caf5a0d6e809886"
    assert len(seen) == 1
    assert seen == {module}


def test_hash_module_simple():
    """Tests that we successfully hash a simple package"""
    from tests.test_package_to_hash import subpackage

    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(subpackage, hash_object, seen_modules)

    assert result.hexdigest() == "7dc5ec7dcfae665257eaae7bdde971da914677e26777ee83c5a3080e824e8d0d"
    assert len(seen_modules) == 1
    assert {m.__name__ for m in seen_modules} == {"tests.test_package_to_hash.subpackage"}


def test_hash_module_with_subpackage():
    """Tests that we successfully hash a simple package that imports a subpackage"""
    from tests.test_package_to_hash import submodule1

    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(submodule1, hash_object, seen_modules)

    assert result.hexdigest() == "b634731cc3037f628e37e91522871245c7f6b2fe9ffad5f0715e7e33324f1b65"
    assert len(seen_modules) == 2
    assert {m.__name__ for m in seen_modules} == {
        "tests.test_package_to_hash.subpackage",
        "tests.test_package_to_hash.submodule1",
    }


def test_hash_module_complex():
    """Tests that we successfully hash submodules and subpackages."""
    from tests import test_package_to_hash

    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(test_package_to_hash, hash_object, seen_modules)

    assert result.hexdigest() == "d91d96366991a8e8aee244c6f72aa7d27f5a9badfae2ab79c1f62694ac9e9fb2"
    assert len(seen_modules) == 4
    assert {m.__name__ for m in seen_modules} == {
        "tests.test_package_to_hash",
        "tests.test_package_to_hash.submodule2",
        "tests.test_package_to_hash.submodule1",
        "tests.test_package_to_hash.subpackage",
    }


def test_hash_module_no_file(caplog):
    """Tests that we successfully hash a module that has no file attribute."""
    caplog.set_level(logging.DEBUG)
    module = ModuleType("mypackage")
    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(module, hash_object, seen_modules)

    assert "Skipping hash" in caplog.text
    assert result.hexdigest() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_hash_module_file_is_none(caplog):
    """Tests that we successfully hash a module that has a file attribute that is None."""
    caplog.set_level(logging.DEBUG)
    module = ModuleType("mypackage")
    module.__file__ = None
    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(module, hash_object, seen_modules)

    assert "Skipping hash" in caplog.text
    assert result.hexdigest() == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
