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

import logging
import os
import shutil
from typing import List

import click
import git

from hamilton.log_setup import setup_logging

setup_logging(logging.INFO)

logger = logging.getLogger(__name__)


def _validate_package_name(name: str) -> str:
    """Validates that the username is a legitimate python variable"""
    if not str.isidentifier(name):
        raise ValueError(
            f"Username {name} is not an importable package name!"
            f" See instructions at the dataflow hub -- "
            f"https://hub.dagworks.io/docs/#checklist-for-new-dataflows"  # noqa E231
        )  # noqa E231
    return name


def _get_base_git_path():
    try:
        repo = git.Repo(".", search_parent_directories=True)
        repo_path = repo.git.rev_parse("--show-toplevel")
        return repo_path
    except git.InvalidGitRepositoryError:
        return None
    except git.NoSuchPathError:
        return None


def _get_contrib_base_path(git_repo_path: str, namespace: str = "user"):
    return os.path.join(git_repo_path, "contrib", "hamilton", "contrib", namespace)


def _get_base_template_dir(base_contrib_path: str):
    return os.path.join(base_contrib_path, "example_dataflow_template")


def _create_username_dir_if_not_exists(
    base_contrib_path: str, sanitized_username: str, username: str
) -> List[str]:
    to_add = []
    username_dir = os.path.join(base_contrib_path, sanitized_username)
    if not os.path.exists(username_dir):
        logger.info(
            f"✅ Creating directory for {username} at {username_dir}, no such directory exists"
        )
        os.mkdir(os.path.join(base_contrib_path, sanitized_username))
    else:
        logger.info(f"Directory for {username} already exists at {username_dir}, no need to create")

    to_add.append(username_dir)

    init_py_location = os.path.join(username_dir, "__init__.py")
    if not os.path.exists(init_py_location):
        logger.info(
            f"✅ Creating __init__.py for {username} at {init_py_location}, no such file exists"
        )
        with open(init_py_location, "w") as f:
            f.write(f'"""{username}\'s dataflows"""\n')
    else:
        logger.info(
            f"✅ __init__.py for {username} already exists at {init_py_location}, no need to create"
        )

    to_add.append(init_py_location)

    base_template_dir = _get_base_template_dir(base_contrib_path)
    author_md_file_path = os.path.join(username_dir, "author.md")
    if not os.path.exists(author_md_file_path):
        logger.info(
            f"✅ Creating author.md for {username} at {author_md_file_path}, no such file exists"
        )
        with open(os.path.join(base_template_dir, "author.md"), "r") as f:
            author_md = f.read()
        with open(os.path.join(username_dir, "author.md"), "w") as f:
            contents = author_md.format(github_username=username)
            contents = (
                contents.replace("---\n", "").replace("title: Example Template\n", "").strip()
            )  # a little hacky, but it'll do
            f.write(contents)
    return to_add


def _create_dataflow_dir_if_not_exists(
    base_contrib_path: str, sanitized_username: str, dataflow_name: str
) -> List[str]:
    to_add = []
    dataflow_dir = os.path.join(base_contrib_path, sanitized_username, dataflow_name)
    if not os.path.exists(dataflow_dir):
        logger.info(
            f"✅ Creating directory for {dataflow_name} at {dataflow_dir}, no such directory exists"
        )
        os.mkdir(dataflow_dir)
    template_dir = os.path.join(_get_base_template_dir(base_contrib_path), "dataflow_template")
    for file_ in [
        "__init__.py",
        "dag.png",
        "README.md",
        "requirements.txt",
        "tags.json",
        "valid_configs.jsonl",
    ]:
        file_path = os.path.join(dataflow_dir, file_)
        if not os.path.exists(file_path):
            copy_from = os.path.join(template_dir, file_)
            logger.info(
                f"✅ Creating file {file_} for {sanitized_username} at {file_path} from {copy_from}"
            )
            shutil.copy(copy_from, file_path)
        else:
            logger.info(
                f"✅ {file_} for {sanitized_username} already exists at {file_path}, no need to create"
            )
        to_add.append(file_path)
    return to_add


def _git_add(files_to_add: List[str], git_repo_path: str):
    repo = git.Repo(git_repo_path)
    repo.index.add(files_to_add)
    logger.info(f"Adding files {files_to_add} to git! Happy developing!")


@click.command()
@click.option("-u", "--username", required=True, help="Username to use for the dataflow")
@click.option(
    "-s",
    "--sanitized-username",
    required=False,
    help="Sanitized username to use for the dataflow -- we will use this for package names. "
    "If not provided, we will use the same username as above.",
    default=None,
)
@click.option("-n", "--dataflow-name", type=_validate_package_name, required=True)
@click.option(
    "-p",
    "--repo-path",
    type=click.Path(exists=True),
    default=_get_base_git_path(),
    help="Path to the git repository to add the dataflow to. Defaults to the "
    "git parent of the current directory",
)
@click.option("-g", "--no-git-add", is_flag=True, help="Don't add the files to git")
def initialize(
    username: str, dataflow_name: str, sanitized_username: str, repo_path: str, no_git_add: bool
):
    if repo_path is None:
        raise ValueError(
            "No git repository found. Please provide the path to the git repository using the "
            "--repo-path flag or run from within your local hamilton clone"
        )
    base_contrib_path = _get_contrib_base_path(repo_path)
    if sanitized_username is None:
        try:
            sanitized_username = _validate_package_name(username)
        except ValueError as e:
            raise ValueError(
                f"Sanitized username not provided and username {username} is not a valid python "
                f"package name. Please provide a valid python package name or a sanitized username "
                f"using the --sanitized-username flag"
            ) from e
    files_to_add = []
    files_to_add.extend(
        _create_username_dir_if_not_exists(base_contrib_path, sanitized_username, username)
    )
    files_to_add.extend(
        _create_dataflow_dir_if_not_exists(base_contrib_path, sanitized_username, dataflow_name)
    )

    if not no_git_add:
        _git_add(files_to_add, repo_path)
