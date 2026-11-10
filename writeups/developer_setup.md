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

# Developer/Contributor Setup

## Repo organization

This repository is organized as follows:

1. hamilton/ is code to orchestrate and execute the graph.
2. tests/ is the place where unit tests (or light integration tests) are located.

## How to contribute

### Set up your local dev environment

Fork this repo and clone your fork. ([GitHub docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks))

```shell
GITHUB_USERNAME="YOUR-GITHUB-USERNAME" \
git clone https://github.com/${GITHUB_USERNAME}/hamilton.git
cd ./hamilton
git remote add upstream https://github.com/apache/hamilton.git
```

Install the project's dependencies with [uv](https://docs.astral.sh/uv/), which is what continuous integration (CI) uses. The `dev` and `test` dependency groups in `pyproject.toml` hold the linting and test tools. They are dependency groups, not extras, so `pip install '.[dev,test]'` does not install them.

```shell
uv sync --group test
```

This creates `.venv` with Hamilton, the `test` group, and the `dev` group, which uv installs by default. Activate it with `. .venv/bin/activate`, or prefix the commands below with `uv run`.

Set up `prek`, which will run some lightweight formatting and linting tasks on every commit.

```shell
prek install
```

### Create a pull request

Make sure your local copy of the `main` branch is up to date with the official `hamilton` repo.

```shell
git checkout main
git pull upstream main

# and might as well update your fork too!
git push origin main
```

Create a new branch.

```shell
git checkout -b feat/some-feature
```

Make changes, commit them, and push them to your fork.

```shell
git push origin HEAD
```

Test your changes locally with `prek`...

```shell
prek run --all-files
```

...and by following the steps in ["How to run unit tests"](#how-to-run-unit-tests).

Navigate to https://github.com/apache/hamilton/pulls and open a pull request.

## How to run unit tests

CI runs on GitHub Actions, and [`.github/workflows/hamilton-main.yml`](../.github/workflows/hamilton-main.yml) holds its commands. Running the same commands locally is the most reliable way to reproduce a CI result.

Install the `test` dependency group, then run the core unit tests as CI's "Test hamilton main package" step does:

```shell
uv sync --group test
uv run pytest tests/ --ignore tests/integrations
```

CI also passes `--cov=hamilton` to measure coverage. A separate step runs `tests/integrations`, with the `pandera` extra and `tests/integrations/pandera/requirements.txt` installed. Other steps test single integrations, such as the plugin tests under `plugin_tests/` (for example `plugin_tests/h_dask`), the Model Context Protocol (MCP) tests, and the OpenLineage tests. Each step installs what it needs on top of the `test` group, for example `uv sync --group test --extra dask`. Read the step in the workflow for its exact commands.

Some tests need more than Python packages:

- The graph-rendering tests in `tests/test_graph.py` run Graphviz's `dot` program. Install Graphviz with your system's package manager (CI runs `apt-get install graphviz` on Linux).
- Some tests in `tests/plugins/test_h_openlineage.py` and `tests/plugins/test_pandas_extensions.py` need a PostgreSQL server named by the `HAMILTON_TEST_POSTGRES_URL` environment variable. They are skipped when it is not set (`tests/conftest.py`).

Optionally, [`scripts/verify`](../scripts/verify) runs the same commands CI runs, one recipe per area. It needs Node 22.18 or newer. `scripts/verify affected` names the checks your change touches, and [`verification/harness.md`](../verification/harness.md) says what the tool assumes.

### Using PyCharm to execute & debug unit tests

You can debug and execute unit tests in PyCharm. To set it up, hit `Edit configurations` and then add New > Python Tests > pytest. Specify the `tests/` folder under `Script path`, and make sure the Python interpreter is the one in `.venv`. If you add `-v` to the additional arguments, you'll get verbose diffs if any tests fail.

# Pushing to pypi
These are the steps to push to pypi. This is taken from the [python packaging tutorial](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives).

1. Have an account & be granted the ability to push to apache-hamilton on testpypi & real pypi.
2. Setup API tokens and add them to your ~/.pypirc.
3. Run `python3 -m pip install --upgrade build`.
4. Run `python3 -m pip install --upgrade twine`
5. Run `python3 -m build` to build Apache Hamilton. It should create things in dist/*.
6. Push to test pypi - `python3 -m twine upload --repository testpypi dist/*`.

   Note: you cannot push the same version twice to test or real pypi. So it's useful to append `-rcX` to the version.
   Once you're happy, you can remove that; just remember to not check that in.
6. Validate you can install from testpypi - follow the URL output.
7. If you can, then push to real pypi. `python3 -m twine upload dist/*`
8. Double check you can download and install what you just pushed in a fresh environment. A good thing to test is to
   run the hello world example.

# Announcing your release

Now that you've pushed to pypi, announce your release! We plan to automate this, but for now...

1. Create a github release (select auto-generate release for painless text generation). Create a tag that's called `apache-hamilton-{version_string}`.
See [1.2.0](https://github.com/apache/hamilton/releases/tag/apache-hamilton-1.2.0) for an example.
2. Announce on the #announcements channel in slack, following the format presented there.
3. Thanks for contributing!

# Pushing to Anaconda
These are the steps to push to Anaconda after you have built and pushed to PyPi successfully.

1. Make sure you have conda installed with conda-build. See [these instructions](https://conda.io/projects/conda-build/en/latest/install-conda-build.html).
Note: since it is common to have pyenv installed too -- conda and pyenv don't play nice. My suggestion is to run
`conda config --set auto_activate_base False` to not set conda to be active by default.
3. Make sure you have an Anaconda account and are authorized to push to anaconda.
4. Log in to anaconda (e.g. conda activate && anaconda login).
5. We have a script `scripts/build_conda.sh` that is a bash script that encapsulates the steps. For reference
it roughly follows [this documentation](https://conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs-skeleton.html).
Run it with `bash scripts/build_conda.sh`. It should "just work".
6. Be sure to remove any files it creates afterwards so when you come to do a release again, you're not uploading the
same files.
