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

Install the project's dependencies in your preferred method for managing python dependencies. For example, run the following to use `venv`.

```shell
python -m venv ./venv
. ./venv/bin/activate

pip install .[dev,test]
```

Please be informed to use escape characters or wrap the argument in quote as shown in the command below since the "[]" or "." may be treated as special characters leading to failure in finding matching files.

```shell
pip install '.[dev,test]'
```

Set up `pre-commit`, which will run some lightweight formatting and linting tasks on every commit.

```shell
pre-commit install
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

Test your changes locally with `pre-commit`...

```shell
pre-commit run --all-files
```

...and by following the steps in ["How to run unit tests"](#how-to-run-unit-tests).

Navigate to https://github.com/apache/hamilton/pulls and open a pull request.

## How to run unit tests

You need to have installed the `requirements-test.txt` dependencies into the environment you're running for this to work. You can run tests two ways:

1. Through pycharm/command line.
2. Using circle ci locally. The config for this lives in `.circleci/config.yml` which also shows commands to run tests
from the command line.

### Running tests in Docker

The most reliable way to run `hamilton`'s unit tests is to simulate its continuous integration (CI) environment in docker.

`hamilton`'s CI logic is defined in shell scripts, whose behavior changes based on environment variable `TASK`.

The following values for `TASK` are recognized:

* `async` = unit tests using the async driver
* `dask` = unit tests using the `dask` adapter
* `integrations` = tests on integrations with other frameworks
* `pre-commit` = static analysis (i.e. linting)
* `pyspark` = unit tests using the `spark` adapter
* `ray` = unit tests using the `ray` adapter
* `tests` = core unit tests with minimal requirements

Choose a Python version and task.

```shell
PYTHON_VERSION='3.8'
TASK=tests
```

Then run the tests for that combination in a container.

```shell
docker run \
  --rm \
  --entrypoint="" \
  -v "$(pwd)":/opt/testing \
  --workdir /opt/testing \
  --env TASK=${TASK} \
  -it circleci/python:${PYTHON_VERSION} \
  /bin/bash -c '.ci/setup.sh && .ci/test.sh'
```

### Using pycharm to execute & debug unit tests

You can debug and execute unit tests in pycharm easily. To set it up, you just hit `Edit configurations` and then
add New > Python Tests > pytest. You then want to specify the `tests/` folder under `Script path`, and ensure the
python environment executing it is the appropriate one with all the dependencies installed. If you add `-v` to the
additional arguments part, you'll then get verbose diffs if any tests fail.

### Using circle ci locally

You need to install the circleci command line tooling for this to work.
See https://circleci.com/docs/local-cli/ for details.
Once you have installed it you just need to run `circleci local execute` from the root directory and it'll run the entire suite of tests
that are setup to run each time you push a commit to a branch in github.

# Pushing to pypi
These are the steps to push to pypi. This is taken from the [python packaging tutorial](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives).

1. Have an account & be granted the ability to push to sf-hamilton on testpypi & real pypi.
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

1. Create a github release (select auto-generate release for painless text generation). Create a tag that's called `sf-hamilton-{version_string}`.
See [1.2.0](https://github.com/apache/hamilton/releases/tag/sf-hamilton-1.2.0) for an example.
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
