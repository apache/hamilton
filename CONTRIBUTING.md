# Guidance on how to contribute

> All contributions to this project will be released under the [Apache 2.0 License](LICENSE). .
> By submitting a pull request or filing a bug, issue, or
> feature request, you are agreeing to comply with this waiver of copyright interest.
> You're also agreeing to abide by the ASF Code of Conduct.


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

## Using circleci CLI to run tests locally

1. Install the [circleci CLI](https://circleci.com/docs/2.0/local-cli/).
2. To run a circleci job locally, you should then, from the root of the repository, do
   > circleci local execute --job=JOB_NAME
3. This assumes you have docker installed, it will pull the images, but otherwise will run the circleci job.
