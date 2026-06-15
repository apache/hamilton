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

"""Tests verifying that the sdist includes examples and does not exclude tests.

Per Apache release policy, voters must be able to build from source
and run tests to validate. Contrib tests live inside the package
(hamilton/contrib/dagworks/*/test_*.py), so the key requirement is
that tests/** is NOT in the exclude list. Examples are included via
a symlink to ../examples/contrib/.
"""

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def get_contrib_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def load_sdist_config() -> dict:
    pyproject = get_contrib_dir() / "pyproject.toml"
    with open(pyproject, "rb") as f:
        config = tomllib.load(f)
    return config["tool"]["flit"]["sdist"]


class TestSdistDoesNotExcludeTests:
    """Verify tests inside the package are not excluded from sdist."""

    def test_tests_not_in_sdist_exclude(self):
        sdist = load_sdist_config()
        excludes = sdist.get("exclude", [])
        assert "tests/**" not in excludes, (
            "pyproject.toml [tool.flit.sdist] must not exclude 'tests/**'. "
            "Apache release policy requires tests in the source tarball. "
            "Contrib tests live inside the package tree."
        )


class TestSdistIncludesExamples:
    """Verify examples are included in the source distribution."""

    def test_examples_in_sdist_include(self):
        sdist = load_sdist_config()
        includes = sdist.get("include", [])
        assert "examples/**" in includes, (
            "pyproject.toml [tool.flit.sdist] must include 'examples/**'. "
            "Examples help voters validate the package works correctly."
        )

    def test_examples_not_in_sdist_exclude(self):
        sdist = load_sdist_config()
        excludes = sdist.get("exclude", [])
        assert "examples/**" not in excludes, (
            "pyproject.toml [tool.flit.sdist] must not exclude 'examples/**'."
        )


class TestSdistIncludesScripts:
    """Verify scripts are included in the source distribution."""

    def test_scripts_in_sdist_include(self):
        sdist = load_sdist_config()
        includes = sdist.get("include", [])
        assert "scripts/**" in includes, (
            "pyproject.toml [tool.flit.sdist] must include 'scripts/**'. "
            "Scripts help voters validate the package (e.g. version_check.py)."
        )


class TestSdistExcludesBinaries:
    """Verify binary files are excluded to keep tarballs source-only."""

    def test_ipynb_excluded(self):
        sdist = load_sdist_config()
        excludes = sdist.get("exclude", [])
        assert "**/*.ipynb" in excludes, (
            "pyproject.toml [tool.flit.sdist] must exclude '**/*.ipynb'. "
            "Notebooks should not be in source tarballs."
        )

    def test_png_excluded(self):
        sdist = load_sdist_config()
        excludes = sdist.get("exclude", [])
        assert "**/*.png" in excludes, (
            "pyproject.toml [tool.flit.sdist] must exclude '**/*.png'. "
            "Binary files should not be in source tarballs."
        )
