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

"""
This file compiles the docs for the hub website.

Basically we want to do the following:
1. For each user, we want to create a folder in the docs/users folder.
2. For each dataflow a user has, we want to create a folder in the user's folder.
3. For each file in the dataflow folder, we want to grab the commits for it.
4. For each dataflow a user has, we pull telemetry data for it. (TODO: once have this).
5. We then want to generate .mdx files and components in the docs/Users/{user}/{dataflow} folder from the
dataflow python files and information we have.
6. We then will trigger a build of the docs; the docs can serve the latest commit version!
"""

import json
import os
import shutil
import subprocess

import jinja2

from hamilton.function_modifiers import config
from hamilton.htypes import Collect, Parallelizable

DATAFLOW_FOLDER = ".."
USER_PATH = DATAFLOW_FOLDER + "/hamilton/contrib/user"
DAGWORKS_PATH = DATAFLOW_FOLDER + "/hamilton/contrib/dagworks"


@config.when(is_dagworks="False")
def user__usr(path: str) -> Parallelizable[dict]:
    """Find all users in the contrib/user folder."""
    for _user in os.listdir(path):
        if (
            os.path.isfile(os.path.join(path, _user))
            or _user.startswith(".")
            or _user.startswith("_")
        ):
            continue
        yield {"user": _user, "path": os.path.join(path, _user)}


@config.when(is_dagworks="True")
def user__dagworks(path: str) -> Parallelizable[dict]:
    """Find all users in the contrib/dagworks folder."""
    yield {"user": "::DAGWORKS::", "path": path}


def dataflows(user: dict) -> list[dict]:
    """Find all dataflows for a user."""
    dataflows = []
    for _dataflow in os.listdir(user["path"]):
        if (
            os.path.isfile(os.path.join(user["path"], _dataflow))
            or _dataflow.startswith(".")
            or _dataflow.startswith("_")
        ):
            continue
        author_md_path = os.path.join(user["path"], "author.md")
        dataflows.append(
            {
                "user": user["user"],
                "author_path": author_md_path,
                "dataflow": _dataflow,
                "path": os.path.join(user["path"], _dataflow),
            }
        )
    return dataflows


def dataflows_with_stats(dataflows: list[dict]) -> list[dict]:
    """Find the latest commit and date for the commit for each file in the dataflow."""
    for dataflow in dataflows:
        # given a dataflow["dataflow"] get stats for it
        dataflow["stats"] = {"downloads": 0, "views": 0}
    return dataflows


def dataflows_with_commits(dataflows: list[dict]) -> list[dict]:
    """Find the latest commit and date for the commit for each file in the dataflow."""
    for dataflow in dataflows:
        for file in os.listdir(dataflow["path"]):
            if file not in [
                "__init__.py",
                "README.md",
                "requirements.txt",
                "valid_configs.jsonl",
                "dag.png",
                "tags.json",
            ]:
                continue
            log_output = (
                subprocess.check_output(
                    [
                        "git",
                        "log",
                        # "-1",
                        "--format='%H %cd'",
                        "--",
                        os.path.join(dataflow["path"], file),
                    ],
                    universal_newlines=True,
                )
                .strip()
                .splitlines()
            )

            # Split the output to get commit hash and commit date
            # print(log_output)
            commit_hashes = []
            commit_dates = []
            for log in log_output:
                commit_hash, commit_date = log.strip("'").split(" ", 1)
                commit_hashes.append(commit_hash)
                commit_dates.append(commit_date)
            dataflow[file] = {"commit": commit_hashes, "timestamp": commit_dates}
            # print(dataflow)
    return dataflows


def dataflows_with_everything(
    dataflows_with_stats: list[dict], dataflows_with_commits: list[dict]
) -> list[dict]:
    """merges the stats and commits into one dict"""
    # naive implementation
    for dataflow in dataflows_with_stats:
        for dataflow_with_commit in dataflows_with_commits:
            if dataflow["dataflow"] == dataflow_with_commit["dataflow"]:
                dataflow.update(dataflow_with_commit)
    return dataflows_with_stats


# TEMPLATES!
template_env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates/"))
builder_template = template_env.get_template("driver_builder.py.jinja2")

mdx_template = """---
id: {USER}-{DATAFLOW_NAME}
title: {DATAFLOW_NAME}
tags: {USE_CASE_TAGS}
---

# {DATAFLOW_NAME}

import CodeBlock from '@theme/CodeBlock';

![dataflow](dag.png)

## To get started:
### Dynamically pull and run
import example from '!!raw-loader!./example1.py';

<CodeBlock language="python">{{example}}</CodeBlock>


### Use published library version
```bash
pip install sf-hamilton-contrib --upgrade  # make sure you have the latest
```

import example2 from '!!raw-loader!./example2.py';

<CodeBlock language="python">{{example2}}</CodeBlock>

### Modify for your needs
Now if you want to modify the dataflow, you can copy it to a new folder (renaming is possible), and modify it there.

<CodeBlock language="python">
dataflows.copy({DATAFLOW_NAME}, "path/to/save/to")
</CodeBlock>

<hr/>

{README}

## Source code

import MyComponentSource from '!!raw-loader!./__init__.py';

<details>
    <summary>__init__.py</summary>
    <CodeBlock language="python">{{MyComponentSource}}</CodeBlock>
</details>

## Requirements
import requirements from '!!raw-loader!./requirements.txt';

<CodeBlock language="text">{{requirements}}</CodeBlock>

"""

mdx_dagworks_template = """---
id: DAGWorks-{DATAFLOW_NAME}
title: {DATAFLOW_NAME}
tags: {USE_CASE_TAGS}
---

# {DATAFLOW_NAME}

import CodeBlock from '@theme/CodeBlock';

![dataflow](dag.png)

## To get started:
### Dynamically pull and run
import example from '!!raw-loader!./example1.py';

<CodeBlock language="python">{{example}}</CodeBlock>


### Use published library version
```bash
pip install sf-hamilton-contrib --upgrade  # make sure you have the latest
```

import example2 from '!!raw-loader!./example2.py';

<CodeBlock language="python">{{example2}}</CodeBlock>

### Modify for your needs
Now if you want to modify the dataflow, you can copy it to a new folder (renaming is possible), and modify it there.

<CodeBlock language="python">
dataflows.copy({DATAFLOW_NAME}, "path/to/save/to")
</CodeBlock>

<hr/>

{README}

## Source code

import MyComponentSource from '!!raw-loader!./__init__.py';

<details>
    <summary>__init__.py</summary>
    <CodeBlock language="python">{{MyComponentSource}}</CodeBlock>
</details>

## Requirements
import requirements from '!!raw-loader!./requirements.txt';

<CodeBlock language="text">{{requirements}}</CodeBlock>

"""
# TODO: edit/adjust links to docs, etc.


@config.when(is_dagworks="False")
def user_dataflows__user(dataflows_with_everything: Collect[list[dict]]) -> dict[str, list[dict]]:
    """Big function that creates the docs for a user."""
    result = {}
    for _user_dataflows in dataflows_with_everything:
        _user_name = _user_dataflows[0]["user"]
        result[_user_name] = _user_dataflows
        # make the folder
        user_path = os.path.join("docs", "Users", _user_name)
        os.makedirs(user_path, exist_ok=True)
        # copy the author.md file
        shutil.copyfile(_user_dataflows[0]["author_path"], os.path.join(user_path, "index.mdx"))
        # make all dataflow folders
        for single_df in _user_dataflows:
            # make the folder
            df_path = os.path.join(user_path, single_df["dataflow"])
            os.makedirs(df_path, exist_ok=True)
            # copy the files
            for file in os.listdir(single_df["path"]):
                if file not in [
                    "__init__.py",
                    "requirements.txt",
                    "valid_configs.jsonl",
                    "dag.png",
                    "tags.json",
                ]:
                    continue
                shutil.copyfile(os.path.join(single_df["path"], file), os.path.join(df_path, file))

            # get tags
            with open(os.path.join(single_df["path"], "tags.json"), "r") as f:
                tags = json.load(f)
            # checks for driver related tags
            uses_executor = tags.get("driver_tags", {}).get("executor", None)
            # create python file
            with open(os.path.join(df_path, "example1.py"), "w") as f:
                f.write(
                    builder_template.render(
                        use_executor=uses_executor,
                        dynamic_import=True,
                        is_user=True,
                        MODULE_NAME=single_df["dataflow"],
                        USER=_user_name,
                    )
                )
            with open(os.path.join(df_path, "example2.py"), "w") as f:
                f.write(
                    builder_template.render(
                        use_executor=uses_executor,
                        dynamic_import=False,
                        is_user=True,
                        MODULE_NAME=single_df["dataflow"],
                        USER=_user_name,
                    )
                )
            # create MDX file
            with open(os.path.join(single_df["path"], "README.md"), "r") as f:
                readme_lines = f.readlines()
            readme_string = ""
            for line in readme_lines:
                readme_string += line.replace("#", "##", 1)

            with open(os.path.join(df_path, "README.mdx"), "w") as f:
                f.write(
                    mdx_template.format(
                        DATAFLOW_NAME=single_df["dataflow"],
                        USER=_user_name,
                        USE_CASE_TAGS=tags["use_case_tags"],
                        README=readme_string,
                    )
                )
            # create commit file -- required for the client to know what commit is latest.
            _create_commit_file(df_path, single_df)

    return result


def _create_commit_file(df_path, single_df):
    commit_path = df_path.replace("docs", "static/commits")
    os.makedirs(commit_path, exist_ok=True)
    with open(os.path.join(commit_path, "commit.txt"), "w") as f:
        for commit, ts in zip(
            single_df["__init__.py"]["commit"], single_df["__init__.py"]["timestamp"]
        ):
            f.write(f"[commit::{commit}][ts::{ts}]\n")


@config.when(is_dagworks="True")
def user_dataflows__dagworks(
    dataflows_with_everything: Collect[list[dict]],
) -> dict[str, list[dict]]:
    """Big function that creates the docs for dagworks dataflow."""
    result = {}
    for _dagworks_dataflows in dataflows_with_everything:
        if len(_dagworks_dataflows) < 1:
            continue
        _user_name = _dagworks_dataflows[0]["user"]
        result[_user_name] = _dagworks_dataflows
        # make the folder
        dagworks_path = os.path.join("docs", "DAGWorks")
        os.makedirs(dagworks_path, exist_ok=True)
        # copy the author.md file
        shutil.copyfile(
            _dagworks_dataflows[0]["author_path"], os.path.join(dagworks_path, "index.mdx")
        )
        # make all dataflow folders
        for single_df in _dagworks_dataflows:
            # make the folder
            df_path = os.path.join(dagworks_path, single_df["dataflow"])
            os.makedirs(df_path, exist_ok=True)
            # copy the files
            for file in os.listdir(single_df["path"]):
                if file not in [
                    "__init__.py",
                    "requirements.txt",
                    "valid_configs.jsonl",
                    "dag.png",
                    "tags.json",
                ]:
                    continue
                shutil.copyfile(os.path.join(single_df["path"], file), os.path.join(df_path, file))
            # get tags
            with open(os.path.join(single_df["path"], "tags.json"), "r") as f:
                tags = json.load(f)
            # checks for driver related tags
            uses_executor = tags.get("driver_tags", {}).get("executor", None)
            # create python file
            with open(os.path.join(df_path, "example1.py"), "w") as f:
                f.write(
                    builder_template.render(
                        use_executor=uses_executor,
                        dynamic_import=True,
                        is_user=False,
                        MODULE_NAME=single_df["dataflow"],
                    )
                )
            with open(os.path.join(df_path, "example2.py"), "w") as f:
                f.write(
                    builder_template.render(
                        use_executor=uses_executor,
                        dynamic_import=False,
                        is_user=False,
                        MODULE_NAME=single_df["dataflow"],
                    )
                )
            # create MDX file
            with open(os.path.join(single_df["path"], "README.md"), "r") as f:
                readme_lines = f.readlines()
            readme_string = ""
            for line in readme_lines:
                readme_string += line.replace("#", "##", 1)

            with open(os.path.join(df_path, "README.mdx"), "w") as f:
                f.write(
                    mdx_dagworks_template.format(
                        DATAFLOW_NAME=single_df["dataflow"],
                        USE_CASE_TAGS=tags["use_case_tags"],
                        README=readme_string,
                    )
                )
            # create commit file -- required for the client to know what commit is latest.
            _create_commit_file(df_path, single_df)

    return result


if __name__ == "__main__":
    import compile_docs  # import this module

    from hamilton import driver
    from hamilton.execution import executors

    # remote_executor = executors.SynchronousLocalTaskExecutor()
    remote_executor = executors.MultiThreadingExecutor(max_tasks=100)
    dr = (
        driver.Builder()
        .with_config(dict(is_dagworks="False"))
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(compile_docs)
        .build()
    )
    res = dr.execute(["user_dataflows"], inputs={"path": USER_PATH})
    # dr.visualize_execution(
    #     ["user_dataflows"],
    #     inputs={"path": USER_PATH},
    #     output_file_path="compile_docs",
    #     render_kwargs={"format": "png"}
    # )
    import pprint

    pprint.pprint(res)

    dr = (
        driver.Builder()
        .with_config(dict(is_dagworks="True"))
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(remote_executor)  # We only need to specify remote executor
        # The local executor just runs it synchronously
        .with_modules(compile_docs)
        .build()
    )
    res = dr.execute(["user_dataflows"], inputs={"path": DAGWORKS_PATH})

    pprint.pprint(res)
