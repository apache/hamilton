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

from hamilton_sdk.driver import _hash_module


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

    assert result.hexdigest() == "3d364e2761d96875e11d0f862c2a5d7299f059ebe429deb94f2112ac243f080f"
    assert len(seen_modules) == 1
    assert {m.__name__ for m in seen_modules} == {"tests.test_package_to_hash.subpackage"}


def test_hash_module_with_subpackage():
    """Tests that we successfully hash a simple package that imports a subpackage"""
    from tests.test_package_to_hash import submodule1

    hash_object = hashlib.sha256()
    seen_modules = set()
    result = _hash_module(submodule1, hash_object, seen_modules)

    assert result.hexdigest() == "4466d1f61b2c57c2b5bfe8a9fec09acd53befcfdf2f5720075aef83e3d6c6bf8"
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

    assert result.hexdigest() == "c22023a4fdc8564de1cda70d05a19d5e8c0ddaaa9dcccf644a2b789b80f19896"
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
