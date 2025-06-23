## Off-the-shelf Apache Hamilton Dataflows

Here you'll find documentation about the sf-hamilton-contrib package that curates a collection of Apache Hamilton Dataflows that are
ready to be used in your own projects. They are user-contributed and maintained, with
the goal of making it easier for you to get started with Apache Hamilton.

We expect this collection to grow over time, so check back often! As dataflows become mature we
will move them into the official sub-package of the respository and become maintained by the
Apache Hamilton team.

### Usage
There are two ways to get access to dataflows in this package. For either approach,
the assumption is that you have the requisite python dependencies installed on your system.
You'll get import errors if you don't. Don't know what you need, we have convenience functions to help!

#### Static installation
This approach relies on you installing the package on your system. This is the recommended path for
production purposes as you can version-lock your dependencies.

To install the package, run:

```bash
pip install sf-hamilton-contrib --upgrade
```

Once installed, you can import the dataflows as follows.

Things you need to know:
1. Whether it's a user or official DAGWorks supported dataflow. If user, what the name of the user is.
2. The name of the dataflow.
```python
from hamilton import driver
# from hamilton.contrib.dagworks import NAME_OF_DATAFLOW
from hamilton.contrib.user.NAME_OF_USER import NAME_OF_DATAFLOW

dr = (
    driver.Builder()
    .with_config({})  # replace with configuration as appropriate
    .with_modules(NAME_OF_DATAFLOW)
    .build()
)
# execute the dataflow, specifying what you want back. Will return a dictionary.
result = dr.execute(
    [NAME_OF_DATAFLOW.FUNCTION_NAME, ...],  # this specifies what you want back
    inputs={...}  # pass in inputs as appropriate
)
```
To find an example [go to the hub](https://hub.dagworks.io/docs/).

#### Dynamic installation
Here we dynamically download the dataflow from the internet and execute it. This is useful for quickly
iterating in a notebook and pulling in just the dataflow you need.

```python
from hamilton import dataflows, driver

# downloads into ~/.hamilton/dataflows and loads the module -- WARNING: ensure you know what code you're importing!
# NAME_OF_DATAFLOW = dataflows.import_module("NAME_OF_DATAFLOW") # if using official DAGWorks dataflow
NAME_OF_DATAFLOW = dataflows.import_module("NAME_OF_DATAFLOW", "NAME_OF_USER")
dr = (
  driver.Builder()
  .with_config({})  # replace with configuration as appropriate
  .with_modules(NAME_OF_DATAFLOW)
  .build()
)
# execute the dataflow, specifying what you want back. Will return a dictionary.
result = dr.execute(
  [NAME_OF_DATAFLOW.FUNCTION_NAME, ...],  # this specifies what you want back
  inputs={...}  # pass in inputs as appropriate
)
```
To find an example [go to the hub](https://hub.dagworks.io/docs/).

#### Modification
Getting started is one thing, but then modifying to your needs is another. So we have a prescribed
flow to enable you to take a dataflow, and copy the code to a place of your choosing. This allows
you to easily modify the dataflow as you see fit.

Run this in a notebook or python script to copy the dataflow to a directory of your choosing.
```python
from hamilton import dataflows

# dynamically pull and then copy
NAME_OF_DATAFLOW = dataflows.import_module("NAME_OF_DATAFLOW", "NAME_OF_USER")
dataflows.copy(NAME_OF_DATAFLOW, destination_path="PATH_TO_DIRECTORY")
# copy from the installed library
from hamilton.contrib.user.NAME_OF_USER import NAME_OF_DATAFLOW
dataflows.copy(NAME_OF_DATAFLOW, destination_path="PATH_TO_DIRECTORY")
```
You can then modify/import the code as you see fit. See [copy()](https://hamilton.apache.org/reference/dataflows/copy/)
for more details.


### How to contribute

If you have a dataflow that you would like to share with the community, please submit a pull request
to this repository. We will review your dataflow and if it meets our standards we will add it to the
package. To submit a pull request please use [this template](https://github.com/apache/hamilton/blob/main/.github/PULL_REQUEST_TEMPLATE/HAMILTON_CONTRIB_PR_TEMPLATE.md)
. To access it, create a new Pull Request, then hit the `preview` tab, and click the link to append `template=HAMILTON_CONTRIB_PR_TEMPLATE.md` to the URL.


#### Dataflow standards
We want to ensure that the dataflows in this package are of high quality and are easy to use. To that end,
we have a set of standards that we expect all dataflows to meet. If you have any questions, please reach out.

Standards:
- The dataflow must be a valid Python module.
- It must not do anything malicious.
- It must be well documented.
- It must work.
- It must follow our standard structure as outlined below.

#### Getting started with development

To get started with development, you'll want to first fork the hamilton repository from the github UI.

Then, clone it locally and install the package in editable mode, ensuring you install any dependencies required for the initilization script
```bash
cd hamilton # Your fork
pip install -e "./contrib[contribute]" # Note that this package lives under the `contrib` folder
```

Next, you need to initialize your dataflow. This will create the necessary files and directories for you to get started.
```bash
init-dataflow -u <your_github_username> -n <name_of_dataflow>
```

This will do the following:

1. Create a package under `contrib/hamilton/contrib/user/<your_github_username>` with the appropriate files to describe you
   -  `author.md` -- this will describe you with links out to github/socials
   - `__init__.py` -- this will be an empty file that allows you to import your dataflow
2. Create a package under `contrib/hamilton/contrib/user/<your_github_username>/<name_of_dataflow>` with the appropriate files to describe your dataflow:
   - `README.md` to describe the dataflow with the standard headings
   - `__init__.py` to contain the Apache Hamilton code
   - `requirements.txt` to contain the required packages outside of Apache Hamilton
   - `tags.json` to curate your dataflow
   - `valid_configs.jsonl` to specify the valid configurations for it to be run
   - `dag.png` to show one possible configuration of your dataflow
3. Add all the above files to git!

These are all required. You do not have to use the initialization script -- you can always copy the files over directly. That said, it is idempotent (it will fill out any missing files),
and will ensure that you have the correct structure.

#### Developing your dataflow

To get started, you'll want to do the following:

- [ ] Fill out your `__init__.py` with the appropriate code -- see [this issue](https://github.com/apache/hamilton/issues/559) if you want some inspiration for where to get started
- [ ] Fill out the sections of your `README.md` with the appropriate documentation -- follow one of the approved dataflows
- [ ] Fill out your `tags.json` with the appropriate tags -- follow one of the approved dataflows
- [ ] Fill out your `valid_configs.jsonl` with the appropriate configurations -- this is not necessary if you have no configurations that can change the shape of your DAG
- [ ] Generate a visual representation of your DAG -- you can use the following `if __name__ == '__main__'` block to do so:
```python
import __init__ as my_module

from hamilton import base, driver

dr = driver.Driver(
    {},
    my_module,
    adapter=base.DefaultAdapter(),
)
# create the DAG image
dr.display_all_functions("dag", {"format": "png", "view": False})
```
- [ ] Push a branch back to your fork
- [ ] Open up a pull request to the main Apache Hamilton repo!
  - [ ] Commit the files we just added
  - [ ] Create a PR
  - [ ] Tag one of the maintainers [elijahbenizzy](https://github.com/elijahbenizzy), [skrawcz](https://github.com/skrawcz), or [zilto](https://github.com/zilto) for a review
  - [ ] Ping us on [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g) if you don't hear back within a few days

#### Username Management

As usernames map to packages, we need to ensure that they are valid. To that end, we have a few rules:
  - [ ] If your username contains hyphens, replace them with underscores.
  - [ ] If your username starts with a number, prefix it with an underscore.
  - [ ] If your author name is a python reserved keyword. Reach out to the maintainers for help.

If the above apply, run the `init-dataflow` command with `-s` to specify a sanitized username.

## Got questions?
Join our [slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g) community to chat/ask Qs/etc.
