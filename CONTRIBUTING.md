
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

# Guidance on how to contribute

> All contributions to this project will be released under the [Apache 2.0 License](LICENSE). .
> By submitting a pull request or filing a bug, issue, or
> feature request, you are agreeing to comply with this waiver of copyright interest.
> You're also agreeing to abide by the ASF Code of Conduct (https://www.apache.org/foundation/policies/conduct.html)


There are two primary ways to help:
 - Using the issue tracker, and
 - Changing the code-base.


## Using the issue tracker

Use the issue tracker to suggest feature requests, report bugs, and ask questions.
This is also a great way to connect with the developers of the project as well
as others who are interested in this solution.

Use the issue tracker to find ways to contribute. Find a bug or a feature, mention in
the issue that you will take on that effort, then follow the _Changing the code-base_
guidance below.


## Changing the code-base

Generally speaking, you should fork this repository, make changes in your
own fork, and then submit a pull request. All new code should have associated
unit tests that validate implemented features and the presence or lack of defects.
Additionally, the code should follow any stylistic and architectural guidelines
prescribed by the project. For us here, this means you install a pre-commit hook and use
the given style files. Basically, you should mimic the styles and patterns in the Apache Hamilton code-base.

In terms of getting setup to develop, we invite you to read our [developer setup guide](developer_setup.md).

## Working with CI dependency locks

Install the uv version in `UV_VERSION` in [the Unit Tests workflow](.github/workflows/hamilton-main.yml)
(`uv --version` shows the installed version). Pull request CI uses this version and the committed
locks. Use `uv sync --locked --group test` for the main test environment and
`uv run --locked prek install` to set up the Git hooks.

After changing dependency metadata, refresh and check the affected locks from the repository root.

```sh
uv lock
uv lock --check
uv lock --project .github/ci/polars1
uv lock --check --project .github/ci/polars1
uv lock --project .github/ci/vaex
uv lock --check --project .github/ci/vaex
```

Commit any changed lock alongside its metadata. To update the CI uv version, change `UV_VERSION`
and the three platform checksums from the [uv release](https://github.com/astral-sh/uv/releases)
in the workflow, then refresh and verify all three locks with that version. Scheduled and manual
canary runs use the latest uv and refresh their copies of the locks.

## Using circleci CLI to run tests locally

1. Install the [circleci CLI](https://circleci.com/docs/2.0/local-cli/).
2. To run a circleci job locally, you should then, from the root of the repository, do
   > circleci local execute --job=JOB_NAME
3. This assumes you have docker installed, it will pull the images, but otherwise will run the circleci job.
