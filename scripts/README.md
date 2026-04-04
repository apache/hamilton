<!--
     Licensed to the Apache Software Foundation (ASF) under one
     or more contributor license agreements.  See the NOTICE file
     distributed with this work for additional information
     regarding copyright ownership.  The ASF licenses this file
     to you under the Apache License, Version 2.0 (the
     "License"); you may not use this file except in compliance
     with the License.  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

     Unless required by applicable law or agreed to in writing,
     software distributed under the License is distributed on an
     "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
     KIND, either express or implied.  See the License for the
     specific language governing permissions and limitations
     under the License.
-->

# Policy on source versus distribution

Apache Hamilton is an apache-incubating project. As such, we intend to follow all Apache guidelines to
both the spirit and (when applicable) the letter.

That said, there is occasional ambiguity. Thus we aim to clarify with a reasonable and consistently maintained
approach. The question that we found most ambiguous when determining our release process is:
1. What counts as source code, and should thus be included in the "sdist" (the source-only distribution)
2. What should be included in the build?

Specifically, we set the following guidelines:

| | source (to vote on) -- tar.gz | sdist -- source used to build | whl file | Reasoning |
|---|---|---|---|---|
| Build Scripts | Y | Y | N | Included in tar.gz and sdist as they are needed to reproduce the build, but not in the whl. These are only meant to be consumed by developers/pod members. |
| Library Source code | Y | Y | Y | Core library source code is included in all three distributions: tar.gz, sdist, and whl. |
| Tests (unit + plugin) | Y | Y | N | We expect users/PMC to download the source distribution, build from source, run the tests, and validate. Thus we include in the tar.gz and sdist, but not in the whl. |
| READMEs | Y | Y | Y | Standard project metadata files (README.md, LICENSE, NOTICE, DISCLAIMER) are included in all three distributions. |
| Documentation | Y | N | N | Documentation source is included in the tar.gz for voters to review, but not in the sdist or whl as it is not needed for building or using the package. |
| Representative Examples | Y | Y | N | A curated set of examples are included in tar.gz and sdist so voters can verify Hamilton works end-to-end. Not in the whl as they serve as documentation/verification only. |
| Other Examples | Y | N | N | These are included in the tar.gz for voters to review but not included in the sdist or whl. |

# Packages

Apache Hamilton consists of 5 independently versioned packages:

| Package | Key | Working Directory | Description |
|---|---|---|---|
| `apache-hamilton` | `hamilton` | `.` | Core library (must be released first) |
| `apache-hamilton-sdk` | `sdk` | `ui/sdk` | Tracking SDK |
| `apache-hamilton-contrib` | `contrib` | `contrib` | Community dataflows |
| `apache-hamilton-ui` | `ui` | `ui/backend` | Web UI server |
| `apache-hamilton-lsp` | `lsp` | `dev_tools/language_server` | Language server |

The core `apache-hamilton` package must be released first. The other four packages depend on it but not on each other.

# Release Process

## Environment Setup

We recommend using [uv](https://docs.astral.sh/uv/) for Python environment management. It handles Python versions, virtual environments, and dependency installation in a single tool.

### Prerequisites

- Python 3.10+
- `uv` ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- `flit` for building
- `twine` for package validation
- GPG key configured for signing
- Node.js + npm for UI builds (only needed for the `ui` package)
- Apache RAT jar for license checking (optional, for verification)

```bash
# Install uv (unless already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a virtual environment with build dependencies
uv venv --python 3.11
uv sync --group release

# Verify GPG setup
gpg --list-secret-keys

# IMPORTANT: set GPG_TTY so GPG can prompt for passphrase
export GPG_TTY=$(tty)
```

Note: all commands below use `uv run` which automatically activates the `.venv` environment.
If you prefer, you can instead `source .venv/bin/activate` and omit the `uv run` prefix.

## Building a Release

The main release script is `scripts/apache_release_helper.py`. It builds the sdist and wheel, signs
all artifacts with GPG, generates SHA512 checksums, uploads to Apache SVN, and generates a vote email template.

```bash
# Release the core package (example: version 1.90.0, RC0)
uv run python scripts/apache_release_helper.py --package hamilton 1.90.0 0 your_apache_id

# Release a downstream package (example: sdk version 0.9.0, RC0)
uv run python scripts/apache_release_helper.py --package sdk 0.9.0 0 your_apache_id
```

The script will:
1. Check prerequisites (`flit`, `twine`, `gpg`)
2. Validate the version in the source matches the version you specified
3. Create a git tag (`apache-hamilton-v1.90.0-incubating-RC0`)
4. Build the sdist (`.tar.gz`) and wheel (`.whl`) using `flit build --no-use-vcs`
5. Validate the wheel with `twine check`
6. Sign all artifacts with GPG and generate SHA512 checksums
7. Upload to Apache SVN dist/dev
8. Print a vote email template

Output lands in the `dist/` directory under the package's working directory.

### Dry Run (no SVN upload)

To test the build and signing without uploading, you can interrupt the script after artifacts
are built (before the SVN upload step), or comment out the upload call. The artifacts will
be in the `dist/` directory for inspection.

### After the Vote Passes

```bash
# Push the git tag
git push origin apache-hamilton-v1.90.0-incubating-RC0

# Upload to PyPI (from the package's working directory)
uv run twine upload dist/apache_hamilton-1.90.0.tar.gz dist/apache_hamilton-1.90.0-py3-none-any.whl
```

# For Voters: Verifying a Release

If you're voting on a release, follow these steps to verify the release candidate.

## Complete Verification Workflow

```bash
# Set version and RC number
export VERSION=1.90.0
export RC=0
export PACKAGE=apache-hamilton  # or apache-hamilton-sdk, etc.

# 1. Download all artifacts from SVN
svn export https://dist.apache.org/repos/dist/dev/incubator/hamilton/${PACKAGE}-${VERSION}-incubating-RC${RC}/ hamilton-rc${RC}
cd hamilton-rc${RC}

# 2. Import KEYS file and verify GPG signatures
wget https://downloads.apache.org/incubator/hamilton/KEYS
gpg --import KEYS

# Verify sdist signature
gpg --verify ${PACKAGE}-${VERSION}-incubating.tar.gz.asc ${PACKAGE}-${VERSION}-incubating.tar.gz

# Verify wheel signature (note: underscores in wheel filenames)
WHEEL_NAME=$(echo ${PACKAGE} | tr '-' '_')-${VERSION}-py3-none-any.whl
gpg --verify ${WHEEL_NAME}.asc ${WHEEL_NAME}

# 3. Verify SHA512 checksums
shasum -a 512 -c ${PACKAGE}-${VERSION}-incubating.tar.gz.sha512
shasum -a 512 -c ${WHEEL_NAME}.sha512

# 4. Extract the source archive and build from source
tar -xzf ${PACKAGE}-${VERSION}-incubating.tar.gz
cd ${PACKAGE}-${VERSION}-incubating/
```

## Build from Source with uv

All remaining steps assume you are inside the extracted source directory
(`${PACKAGE}-${VERSION}-incubating/`) from the step above.

```bash
# Create a fresh environment and install build tools
uv venv --python 3.11 --clean
uv sync --group release

# Build the wheel from source
uv run flit build --no-use-vcs

# Install the wheel you just built
uv pip install dist/apache_hamilton-${VERSION}-py3-none-any.whl
```

## Run Tests

```bash
# Install test dependencies (uses the test dependency group from pyproject.toml)
uv sync --group test

# Run core unit tests
uv run pytest tests/ -x -q

# Run plugin tests
uv run pytest plugin_tests/ -x -q
```

## Run Examples

The source archive includes representative examples to verify Hamilton works end-to-end. Each example may require additional dependencies.

### Hello World (no extra deps)
```bash
cd examples/hello_world
uv run python my_script.py
cd ../..
```

### Data Quality with Pandera
```bash
uv pip install pandera
cd examples/data_quality/simple
uv run python run.py
cd ../../..
```

### Function Reuse
```bash
cd examples/reusing_functions
uv run python run.py
cd ../..
```

### Schema Validation
```bash
cd examples/schema
uv run python run.py
cd ../..
```

### Materialization (Pandas)
```bash
uv pip install openpyxl xlsxwriter
cd examples/pandas/materialization
uv run python run.py
cd ../../..
```

## Verification Script

For automated verification of signatures, checksums, and license compliance, use the verification script.
Run these from inside the extracted source directory (`${PACKAGE}-${VERSION}-incubating/`).

### Prerequisites

Download Apache RAT for license verification (into the extracted source directory):

```bash
curl -O https://repo1.maven.org/maven2/org/apache/rat/apache-rat/0.15/apache-rat-0.15.jar
```

### Running Verification

```bash
# Run from the extracted source directory (${PACKAGE}-${VERSION}-incubating/)
# Verify GPG signatures and SHA512 checksums
uv run python scripts/verify_apache_artifacts.py signatures

# Verify license headers (requires Apache RAT)
uv run python scripts/verify_apache_artifacts.py licenses --rat-jar apache-rat-0.15.jar

# Verify everything
uv run python scripts/verify_apache_artifacts.py all --rat-jar apache-rat-0.15.jar

# Inspect artifact contents
uv run python scripts/verify_apache_artifacts.py list-contents dist/apache-hamilton-1.90.0-incubating.tar.gz
uv run python scripts/verify_apache_artifacts.py list-contents dist/apache_hamilton-1.90.0-py3-none-any.whl

# Validate wheel metadata
uv run python scripts/verify_apache_artifacts.py twine-check
```

# Local Development

For local wheel building/testing without signing or the full release process:

```bash
uv venv --python 3.11
uv sync --group release

# Build both sdist and wheel
uv run flit build --no-use-vcs

# Or just the wheel
uv run flit build --no-use-vcs --format wheel

# Install and test locally
uv pip install dist/apache_hamilton-*.whl
uv run python -c "import hamilton; print(hamilton.version.VERSION)"
```
