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
import logging
from types import ModuleType
from unittest.mock import mock_open, patch

from hamilton_sdk.driver import (
    RESULT_BUILDER_NODE_NAME,
    _extract_node_templates_from_function_graph,
    _hash_module,
    hash_dag,
)


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


def _basic_function_graph():
    from hamilton import graph

    from tests.resources import basic_dag_with_config

    return graph.FunctionGraph.from_modules(basic_dag_with_config, config={"foo": "bar"})


def _function_graph_with_a_colliding_node():
    """A graph containing a real node named ``_result_builder``, via an external input."""
    from hamilton import graph

    from tests.resources import dag_with_reserved_node_name

    return graph.FunctionGraph.from_modules(dag_with_reserved_node_name, config={})


def test_extract_node_templates_appends_result_builder():
    """The synthetic result builder node is appended when the caller asks for it."""
    fg = _basic_function_graph()
    templates = _extract_node_templates_from_function_graph(fg, include_result_builder=True)

    assert len(templates) == len(fg.nodes) + 1
    result_builder = templates[-1]
    assert result_builder["name"] == RESULT_BUILDER_NODE_NAME
    assert result_builder["classifications"] == ["result_builder"]
    # Deps are per-run (the requested outputs), so the template carries none.
    assert result_builder["dependencies"] == []
    assert result_builder["code_artifact_pointers"] == []
    assert result_builder["output"] == {"type_name": "typing.Any"}
    # It must not shadow a real node.
    assert RESULT_BUILDER_NODE_NAME not in fg.nodes


def test_extract_node_templates_omits_result_builder_by_default():
    """Only callers that also emit a task run should register the node.

    The legacy ``hamilton_sdk.driver.Driver`` shares this function but emits no task run, so
    registering the node there would leave every run rendering a node that never executes.
    """
    fg = _basic_function_graph()
    templates = _extract_node_templates_from_function_graph(fg)

    assert len(templates) == len(fg.nodes)
    assert RESULT_BUILDER_NODE_NAME not in {t["name"] for t in templates}


def test_result_builder_node_is_skipped_when_the_name_is_taken(caplog):
    """A second template of the same name would fail registration, so the node is dropped."""
    fg = _function_graph_with_a_colliding_node()
    assert RESULT_BUILDER_NODE_NAME in fg.nodes, "test graph does not reproduce the collision"

    templates = _extract_node_templates_from_function_graph(fg, include_result_builder=True)

    assert len(templates) == len(fg.nodes)
    assert len([t for t in templates if t["name"] == RESULT_BUILDER_NODE_NAME]) == 1
    assert "Not registering the synthetic _result_builder node" in caplog.text


def test_result_builder_node_changes_the_dag_hash():
    """The hash identifies the template, so it has to move when the node set does."""
    fg = _basic_function_graph()
    assert hash_dag(fg, include_result_builder=True) != hash_dag(fg)


def test_dag_hash_is_unchanged_when_the_name_is_taken():
    """No node registered means no new template -- the three uses have to agree."""
    fg = _function_graph_with_a_colliding_node()
    assert hash_dag(fg, include_result_builder=True) == hash_dag(fg)
