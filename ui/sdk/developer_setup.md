# Developer/Contributor Setup

## Repo organization

This repository is organized as follows:

1. src/dagworks/ is cli and driver code.
2. tests/ is the place where unit tests (or light integration tests) are located.

## How to contribute

### Set up your local dev environment

Fork this repo and clone your fork.
([GitHub docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks))

```shell
GITHUB_USERNAME="YOUR-GITHUB-USERNAME" \
git clone https://github.com/${GITHUB_USERNAME}/hamilton-sdk.git
cd ./hamilton-sdk
git remote add upstream https://github.com/apache/hamilton-sdk.git
```

Install the project's dependencies in your preferred method for managing python dependencies.
For example, run the following to use `venv`.

```shell
python -m venv ./venv
. ./venv/bin/activate

pip install \
    -r ./requirements.txt \
    -r ./requirements-dev.txt \
    -r ./requirements-test.txt
```

Set up `pre-commit`, which will run some lightweight formatting and linting tasks on every commit.

```shell
pre-commit install
```

### Create a pull request

Make sure your local copy of the `main` branch is up to date with the official `hamilton-sdk` repo.

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

Navigate to https://github.com/apache/hamilton-sdk/pulls and open a pull request.

## How to run unit tests

You need to have installed the `requirements-test.txt` dependencies into the environment you're
running for this to work. You can run tests two ways:

1. Through pycharm/command line.
2. Via the github actions.

### Using pycharm to execute & debug unit tests

You can debug and execute unit tests in pycharm easily. To set it up, you just hit
`Edit configurations` and then add New > Python Tests > pytest. You then want to specify the
`tests/` folder under `Script path`, and ensure the python environment executing it is the
appropriate one with all the dependencies installed. If you add `-v` to the
additional arguments part, you'll then get verbose diffs if any tests fail.

# Pushing to pypi
These are the steps to push to pypi. This is taken from the
[python packaging tutorial](https://packaging.python.org/tutorials/packaging-projects/#generating-distribution-archives).

1. Have an account & be granted the ability to push to hamilton-sdk on testpypi & real pypi.
2. Setup API tokens and add them to your ~/.pypirc.
3. Run `python3 -m pip install --upgrade build`.
4. Run `python3 -m pip install --upgrade twine`
5. Run `python3 -m build` to build hamilton-sdk. It should create things in dist/*.
6. Push to test pypi - `python3 -m twine upload --repository testpypi dist/*`.
   Note: you cannot push the same version twice to test or real pypi. So it's useful to append `-rcX` to the version.
   Once you're happy, you can remove that; just remember to not check that in.
6. Validate you can install from testpypi - follow the URL output.
7. If you can, then push to real pypi. `python3 -m twine upload dist/*`
8. Double check you can download and install what you just pushed in a fresh environment. A good thing to test is to
   run the hello world example.

# Pushing to Anaconda
These are the steps to push to Anaconda after you have built and pushed to PyPi successfully.

1. Make sure you have conda installed with conda-build. See [these instructions](https://conda.io/projects/conda-build/en/latest/install-conda-build.html).
Note: since it is common to have pyenv installed too -- conda and pyenv don't play nice. My suggestion is to run
`conda config --set auto_activate_base False` to not set conda to be active by default.
3. Make sure you have an Anaconda account and are authorized to push to anaconda.
4. Log in to anaconda (e.g. conda activate && anaconda login).
5. We have a script bash script that encapsulates the steps. For reference
it roughly follows [this documentation](https://conda.io/projects/conda-build/en/latest/user-guide/tutorials/build-pkgs-skeleton.html).
6. Be sure to remove any files it creates afterwards so when you come to do a release again, you're not uploading the
same files.
