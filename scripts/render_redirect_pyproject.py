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

"""Render a redirect package's pyproject.toml from its template and its source package.

The sf-hamilton* redirect packages keep their old PyPI names installing the apache-hamilton*
packages. Each redirect must depend on its source package, offer the same extras and accept the
same Python versions, so none of these is written in its template: this script reads them from
the source package's pyproject.toml when the redirect is built.

Usage: render_redirect_pyproject.py REDIRECT_DIR VERSION

Writes REDIRECT_DIR/pyproject.toml. VERSION must be the source package's version in this
checkout, so the redirect's extras and Python versions are those of the release it points to.
"""

import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Each redirect directory, and the pyproject.toml of the package it redirects to.
SOURCES = {
    "sf-hamilton-redirect": "pyproject.toml",
    "sf-hamilton-contrib-redirect": "contrib/pyproject.toml",
    "sf-hamilton-lsp-redirect": "dev_tools/language_server/pyproject.toml",
    "sf-hamilton-sdk-redirect": "ui/sdk/pyproject.toml",
    "sf-hamilton-ui-redirect": "ui/backend/pyproject.toml",
}


def source_project(redirect_dir: Path) -> dict:
    """The [project] table of the package `redirect_dir` redirects to."""
    return tomllib.loads((REPO / SOURCES[redirect_dir.name]).read_text())["project"]


def render(redirect_dir: Path, version: str) -> str:
    """The redirect's pyproject.toml for `version`, from its template and its source package."""
    source = source_project(redirect_dir)
    template = (redirect_dir / "pyproject.toml.template").read_text()
    text = template.replace("SOURCE_NAME", source["name"])
    text = text.replace("REQUIRES_PYTHON", source["requires-python"])
    text = text.replace("VERSION", version)
    extras = source.get("optional-dependencies", {})
    if extras:
        lines = [f'{extra} = ["{source["name"]}[{extra}]=={version}"]' for extra in extras]
        text += "\n[project.optional-dependencies]\n" + "\n".join(lines) + "\n"
    return text


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    redirect_dir, version = Path(argv[1]).resolve(), argv[2]
    source = source_project(redirect_dir)
    if source["version"] != version:
        print(
            f"error: {SOURCES[redirect_dir.name]} is {source['name']} {source['version']}, "
            f"not {version}. Build the redirect from a checkout of the release it points to.",
            file=sys.stderr,
        )
        return 1
    (redirect_dir / "pyproject.toml").write_text(render(redirect_dir, version))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
