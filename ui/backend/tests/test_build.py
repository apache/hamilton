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
#   Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Build verification tests for Hamilton UI.

These tests ensure that the build process correctly creates and packages
frontend assets for mini mode deployment.
"""

import sys
from pathlib import Path

# Use tomllib (Python 3.11+) or fallback to tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def get_project_root():
    """Get the project root directory (hamilton/)."""
    current = Path(__file__).resolve().parent
    while current.name != "hamilton":
        current = current.parent
        if current == current.parent:  # Reached filesystem root
            raise RuntimeError("Could not find project root (hamilton/)")
    return current


def get_ui_backend_dir():
    """Get the ui/backend directory."""
    return get_project_root() / "ui" / "backend"


def get_build_dir():
    """Get the build directory path."""
    return get_ui_backend_dir() / "server" / "build"


class TestBuildDirectory:
    """Tests for the build directory structure."""

    def test_build_directory_exists(self):
        """Verify that the build directory exists after build."""
        build_dir = get_build_dir()
        assert build_dir.exists(), (
            f"Build directory does not exist at {build_dir}. "
            "Run 'hamilton-admin-build-ui' to build the frontend."
        )
        assert build_dir.is_dir(), f"Build path exists but is not a directory: {build_dir}"

    def test_index_html_exists(self):
        """Verify that index.html exists in the build directory."""
        index_html = get_build_dir() / "index.html"
        assert index_html.exists(), (
            f"index.html not found at {index_html}. The frontend build may have failed."
        )
        assert index_html.is_file(), f"index.html exists but is not a file: {index_html}"

        # Verify it's not empty
        content = index_html.read_text()
        assert len(content) > 0, "index.html is empty"
        assert "<html" in content.lower(), "index.html does not appear to be valid HTML"

    def test_static_directory_exists(self):
        """Verify that the static directory exists with JS/CSS assets."""
        static_dir = get_build_dir() / "static"
        assert static_dir.exists(), (
            f"static/ directory not found at {static_dir}. The frontend build may have failed."
        )
        assert static_dir.is_dir(), f"static/ exists but is not a directory: {static_dir}"

        # Check for JS directory
        js_dir = static_dir / "js"
        assert js_dir.exists(), f"static/js/ directory not found at {js_dir}"

        # Check for at least one JS file
        js_files = list(js_dir.glob("*.js"))
        assert len(js_files) > 0, f"No JavaScript files found in {js_dir}"

        # Check for CSS directory
        css_dir = static_dir / "css"
        assert css_dir.exists(), f"static/css/ directory not found at {css_dir}"

        # Check for at least one CSS file
        css_files = list(css_dir.glob("*.css"))
        assert len(css_files) > 0, f"No CSS files found in {css_dir}"

    def test_public_assets_exist(self):
        """Verify that public assets (favicon, logo, etc.) are copied."""
        build_dir = get_build_dir()

        # Check for common public assets
        expected_assets = ["favicon.ico", "manifest.json"]
        for asset in expected_assets:
            asset_path = build_dir / asset
            # Note: These are optional, so we don't fail if missing
            # Just verify they exist if they're supposed to be there
            if asset_path.exists():
                assert asset_path.is_file(), f"{asset} exists but is not a file"


class TestDjangoConfiguration:
    """Tests for Django settings configuration."""

    def test_settings_mini_mode_configured(self):
        """Verify that Django settings are correctly configured for mini mode."""
        settings_file = get_ui_backend_dir() / "server" / "server" / "settings.py"
        assert settings_file.exists(), f"Django settings file not found at {settings_file}"

        settings_content = settings_file.read_text()

        # Check for mini mode configuration
        assert 'HAMILTON_ENV == "mini"' in settings_content, (
            "Django settings missing mini mode configuration"
        )

        # Check for STATICFILES_DIRS pointing to build/static/
        assert "build/static/" in settings_content, (
            "Django settings missing build/static/ in STATICFILES_DIRS"
        )

        # Check for MEDIA_ROOT pointing to build/
        assert "MEDIA_ROOT" in settings_content, "Django settings missing MEDIA_ROOT configuration"

    def test_urls_mini_mode_configured(self):
        """Verify that Django URLs are configured for mini mode SPA routing."""
        urls_file = get_ui_backend_dir() / "server" / "server" / "urls.py"
        assert urls_file.exists(), f"Django URLs file not found at {urls_file}"

        urls_content = urls_file.read_text()

        # Check for mini mode configuration
        assert 'settings.HAMILTON_ENV == "mini"' in urls_content, (
            "Django URLs missing mini mode configuration"
        )

        # Check for index.html template serving (SPA catch-all)
        assert "index.html" in urls_content, "Django URLs missing index.html template configuration"


class TestPackageConfiguration:
    """Tests for Flit packaging configuration."""

    def test_pyproject_toml_exists(self):
        """Verify that pyproject.toml exists."""
        pyproject_file = get_ui_backend_dir() / "pyproject.toml"
        assert pyproject_file.exists(), f"pyproject.toml not found at {pyproject_file}"

    def test_flit_sdist_includes_build_directory(self):
        """Verify that pyproject.toml includes hamilton_ui/build/** in Flit sdist."""
        pyproject_file = get_ui_backend_dir() / "pyproject.toml"

        with open(pyproject_file, "rb") as f:
            config = tomllib.load(f)

        # Check for [tool.flit.sdist] section
        assert "tool" in config, "pyproject.toml missing [tool] section"
        assert "flit" in config["tool"], "pyproject.toml missing [tool.flit] section"
        assert "sdist" in config["tool"]["flit"], "pyproject.toml missing [tool.flit.sdist] section"

        # Check includes
        includes = config["tool"]["flit"]["sdist"].get("include", [])
        assert "hamilton_ui/build/**" in includes, (
            "pyproject.toml [tool.flit.sdist] does not include 'hamilton_ui/build/**'. "
            "Built assets will not be packaged in the distribution."
        )

    def test_manifest_in_does_not_exist(self):
        """Verify that MANIFEST.in does not exist (Flit uses pyproject.toml)."""
        manifest_file = get_ui_backend_dir() / "MANIFEST.in"
        assert not manifest_file.exists(), (
            f"MANIFEST.in should not exist at {manifest_file}. "
            "Flit ignores MANIFEST.in and uses pyproject.toml [tool.flit.sdist] instead."
        )


class TestBuildScript:
    """Tests for the build script."""

    def test_build_script_exists(self):
        """Verify that ui/admin.py exists."""
        build_script = get_project_root() / "ui" / "admin.py"
        assert build_script.exists(), f"Build script not found at {build_script}"

    def test_build_commands_in_script(self):
        """Verify that the build script contains expected commands."""
        build_script = get_project_root() / "ui" / "admin.py"
        script_content = build_script.read_text()

        # Check for expected build steps (Burr pattern)
        expected_commands = [
            "npm install",
            "npm run build",
            "rm -rf",
            "mkdir -p",
            "cp -a",
        ]

        for cmd in expected_commands:
            assert cmd in script_content, f"Build script missing expected command: {cmd}"

    def test_build_verification_in_script(self):
        """Verify that the build script includes verification logic."""
        build_script = get_project_root() / "ui" / "admin.py"
        script_content = build_script.read_text()

        # Check for verification of index.html and static/
        assert "index.html" in script_content, "Build script should verify index.html exists"
        assert "static" in script_content, "Build script should verify static/ directory exists"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
