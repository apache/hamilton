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

# Scripts Reference

| Script | Purpose |
|---|---|
| `scripts/apache_release_helper.py` | Build artifacts, sign, tag, upload RC to SVN, generate vote email |
| `scripts/promote_rc.sh` | Move a voted RC from SVN dev to SVN release |
| `scripts/verify_apache_artifacts.py` | Verify GPG signatures, checksums, and license headers |
| `scripts/verification-script.sh` | End-to-end RC validation (download, verify, build, test, examples) |
| `scripts/generate_announce_email.py` | Generate vote result, announcement email, and Slack message |
| `scripts/qualify.sh` | Run a sampling of examples for quick qualification |
| `scripts/setup_keys.sh` | Set up GPG keys for signing |
| `sf-hamilton-redirect/build.sh` | Build the `sf-hamilton` redirect package for a given version |

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

Set these variables for the release you're building:

```bash
export VERSION=1.90.0
export RC=0
export PACKAGE_KEY=hamilton  # one of: hamilton, sdk, lsp, contrib, ui
export APACHE_ID=your_apache_id
```

The main release script is `scripts/apache_release_helper.py`:

```bash
uv run python scripts/apache_release_helper.py \
    --package ${PACKAGE_KEY} ${VERSION} ${RC} ${APACHE_ID}
```

The script will:
1. Check prerequisites (`flit`, `gpg`, `svn`)
2. Validate the version in the source matches the version you specified
3. Create a git tag (e.g., `apache-hamilton-v${VERSION}-incubating-RC${RC}`)
4. Build the sdist (`.tar.gz`) and wheel (`.whl`) using `flit build --no-use-vcs`
5. Validate the wheel with `twine check`
6. Sign all artifacts with GPG and generate SHA512 checksums
7. Upload to Apache SVN dist/dev
8. Print a vote email template

Output lands in the `dist/` directory under the package's working directory.

### Dry Run

To build and sign artifacts without uploading to SVN or creating a git tag:

```bash
uv run python scripts/apache_release_helper.py \
    --package ${PACKAGE_KEY} ${VERSION} ${RC} ${APACHE_ID} --dry-run
```

### After the Vote Passes

Once the vote passes, follow these steps to finalize the release.
If you don't have the variables from the build step, set them:

```bash
export VERSION=1.90.0
export RC=0
export PACKAGE_KEY=hamilton
export APACHE_ID=your_apache_id
```

Derived variables used below:

```bash
export PACKAGE=apache-${PACKAGE_KEY}  # e.g., apache-hamilton
export TAG="${PACKAGE}-v${VERSION}-incubating-RC${RC}"
```

#### 1. Promote RC artifacts to the release SVN

```bash
# Dry run first to verify
scripts/promote_rc.sh --dry-run ${PACKAGE} ${VERSION} ${RC}

# Then promote for real
scripts/promote_rc.sh ${PACKAGE} ${VERSION} ${RC}
```

#### 2. Upload to PyPI

```bash
PACKAGE_UNDERSCORE=$(echo ${PACKAGE} | tr '-' '_')
twine upload dist/${PACKAGE_UNDERSCORE}-${VERSION}-py3-none-any.whl dist/${PACKAGE}-${VERSION}-incubating-src.tar.gz
```

#### 3. Build and upload the sf-hamilton redirect package

The `sf-hamilton` package on PyPI is a thin redirect that depends on `apache-hamilton`.
This ensures existing users who `pip install sf-hamilton` get the new release, and that
all extras (e.g., `sf-hamilton[dask]`, `sf-hamilton[mcp]`) continue to work.

The `sf-hamilton-redirect/` directory contains a `pyproject.toml.template` with `VERSION`
as a placeholder. The build script stamps in the real version, builds, and validates:

```bash
sf-hamilton-redirect/build.sh ${VERSION}

# Upload
twine upload sf-hamilton-redirect/dist/sf_hamilton-${VERSION}*
```

#### 4. Sanity check the PyPI uploads

```bash
# Test apache-hamilton in a fresh env
pip install apache-hamilton==${VERSION}
python -c "import hamilton; print(hamilton.version.VERSION)"

# Test sf-hamilton redirect (base + an extra)
pip install sf-hamilton[visualization]==${VERSION}
python -c "import hamilton; import graphviz; print('OK')"
```

#### 5. Send announcement emails

```bash
python scripts/generate_announce_email.py \
    --package ${PACKAGE_KEY} --version ${VERSION} --rc ${RC} \
    --tag ${TAG} \
    --binding-votes 3 --nonbinding-votes 1
```

This generates three outputs:
- **[RESULT][VOTE]** email for `dev@hamilton.apache.org`
- **[ANNOUNCE]** email for `user@hamilton.apache.org`
- **Slack message** for copy-paste

#### 6. Squash-merge the release branch back to main

```bash
git checkout main
git merge --squash release/hamilton/${VERSION}
git commit -m "Release apache-hamilton ${VERSION}"
git push origin main
```

# For Voters: Verifying a Release

If you're voting on a release, you can either use the automated script or follow the
manual steps below.

## Automated Verification

The `scripts/verification-script.sh` script runs all verification steps end-to-end:
downloads from SVN, verifies signatures/checksums, checks license headers, builds
from source, runs tests, and exercises examples.

```bash
scripts/verification-script.sh <version> <rc>
# e.g., scripts/verification-script.sh 1.90.0 0
```

## Manual Verification

### Step 1: Download the Artifacts

```bash
# Set version and RC number
export VERSION=1.90.0  # adjust to the version being voted on
export RC=0
export PACKAGE=apache-hamilton  # or apache-hamilton-sdk, etc.

# Derived names (dashes for tarball, underscores for wheel)
export SRC_TAR=${PACKAGE}-${VERSION}-incubating-src.tar.gz
export WHEEL_NAME=$(echo ${PACKAGE} | tr '-' '_')-${VERSION}-py3-none-any.whl
export EXTRACTED_DIR=$(echo ${PACKAGE} | tr '-' '_')-${VERSION}

# Download all artifacts from SVN
svn export https://dist.apache.org/repos/dist/dev/incubator/hamilton/${PACKAGE}/${VERSION}-RC${RC}/ hamilton-rc${RC}
cd hamilton-rc${RC}

# Import the KEYS file
wget https://downloads.apache.org/incubator/hamilton/KEYS
gpg --import KEYS
```

### Step 2: Extract and Set Up

```bash
# Extract the source archive
tar -xzf ${SRC_TAR}
cd ${EXTRACTED_DIR}/

# Create a fresh environment and install build tools
uv venv --python 3.11 --clean
uv sync --group release

# Download Apache RAT for license verification
curl -O https://repo1.maven.org/maven2/org/apache/rat/apache-rat/0.15/apache-rat-0.15.jar
```

### Step 3: Run Automated Verification

The verification script checks GPG signatures, SHA512 checksums, and Apache license headers in one command.
The script looks for artifacts in a `dist/` directory by default, so first copy them there:

```bash
# Copy artifacts into dist/ so the verification script can find them
mkdir -p dist
cp ../${SRC_TAR}* dist/
cp ../${WHEEL_NAME}* dist/

# Verify everything (signatures + checksums + license headers)
uv run python scripts/verify_apache_artifacts.py all --rat-jar apache-rat-0.15.jar
```

You can also run individual checks:

```bash
# Signatures and checksums only
uv run python scripts/verify_apache_artifacts.py signatures

# License headers only
uv run python scripts/verify_apache_artifacts.py licenses --rat-jar apache-rat-0.15.jar

# Validate wheel metadata
uv run python scripts/verify_apache_artifacts.py twine-check

# Inspect artifact contents
uv run python scripts/verify_apache_artifacts.py list-contents dist/${SRC_TAR}
uv run python scripts/verify_apache_artifacts.py list-contents dist/${WHEEL_NAME}
```

### Step 4: Build from Source

```bash
# Build the wheel from source
uv run flit build --no-use-vcs

# Install the wheel you just built
uv pip install dist/${WHEEL_NAME}
```

### Step 5: Run Tests

```bash
# Install test dependencies
uv sync --group test

# Run core unit tests
uv run pytest tests/ -x -q

# Run plugin tests
# Note: some plugin tests require optional dependencies (ray, spark, vaex).
# Exclude any that are not installed in your environment:
uv run pytest plugin_tests/ -x -q \
    --ignore=plugin_tests/h_ray \
    --ignore=plugin_tests/h_spark \
    --ignore=plugin_tests/h_vaex
```

### Step 6: Run Examples

The source archive includes representative examples to verify Hamilton works end-to-end.

```bash
# Hello World (no extra deps)
uv run python examples/hello_world/my_script.py

# Data Quality with Pandera (must run from its directory for CSV data file)
cd examples/data_quality/simple
uv run python run.py
cd ../../..

# Function Reuse
uv run python examples/reusing_functions/main.py

# Schema Validation
uv run python examples/schema/dataflow.py

# Materialization (Pandas)
uv run python examples/pandas/materialization/my_script.py
```

### Manual Signature Verification (alternative to Step 3)

If you prefer to verify signatures and checksums manually instead of using the verification script:

```bash
# From the hamilton-rc${RC}/ directory (before extracting)

# Verify GPG signatures
gpg --verify ${SRC_TAR}.asc ${SRC_TAR}
gpg --verify ${WHEEL_NAME}.asc ${WHEEL_NAME}

# Verify SHA512 checksums
# Note: the .sha512 files contain only the raw hash (no filename),
# so `shasum -c` won't work. Compare hashes manually instead:
echo "$(cat ${SRC_TAR}.sha512)  ${SRC_TAR}" | shasum -a 512 -c -
echo "$(cat ${WHEEL_NAME}.sha512)  ${WHEEL_NAME}" | shasum -a 512 -c -
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
