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

"""The sf-hamilton* redirect packages offer what the packages they redirect to declare."""

import importlib.util
import tomllib
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet

REPO = Path(__file__).resolve().parent.parent
REDIRECT_DIRS = sorted(REPO.glob("sf-hamilton*-redirect"))
VERSION = "1.90.0"

# The apache-hamilton source distribution, which release voters test from, holds this test but
# neither the redirect directories nor every package they redirect to.
pytestmark = pytest.mark.skipif(
    not (REPO / "sf-hamilton-redirect").is_dir(),
    reason="the redirect packages are only in a full checkout of the repository",
)


@pytest.fixture(scope="module")
def renderer():
    spec = importlib.util.spec_from_file_location(
        "render_redirect_pyproject", REPO / "scripts" / "render_redirect_pyproject.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_redirect_directory_names_its_source(renderer):
    assert sorted(d.name for d in REDIRECT_DIRS) == sorted(renderer.SOURCES)


@pytest.mark.parametrize("redirect_dir", REDIRECT_DIRS, ids=lambda d: d.name)
def test_redirect_matches_its_source(redirect_dir, renderer):
    source = renderer.source_project(redirect_dir)
    rendered = tomllib.loads(renderer.render(redirect_dir, VERSION))["project"]

    assert rendered["name"] == source["name"].replace("apache-", "sf-", 1)
    assert rendered["version"] == VERSION
    assert rendered["dependencies"] == [f"{source['name']}=={VERSION}"]
    assert SpecifierSet(rendered["requires-python"]) == SpecifierSet(source["requires-python"])
    assert rendered.get("optional-dependencies", {}) == {
        extra: [f"{source['name']}[{extra}]=={VERSION}"]
        for extra in source.get("optional-dependencies", {})
    }


@pytest.mark.parametrize("redirect_dir", REDIRECT_DIRS, ids=lambda d: d.name)
def test_build_refuses_a_version_its_source_does_not_declare(redirect_dir, renderer, capsys):
    source = renderer.source_project(redirect_dir)
    rendered = redirect_dir / "pyproject.toml"
    before = rendered.read_text() if rendered.exists() else None

    assert renderer.main(["render_redirect_pyproject.py", str(redirect_dir), "0.0.0a0"]) == 1

    error = capsys.readouterr().err
    assert f"{source['name']} {source['version']}" in error
    assert "0.0.0a0" in error
    assert (rendered.read_text() if rendered.exists() else None) == before
