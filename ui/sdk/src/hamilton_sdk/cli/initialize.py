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

import importlib.resources
import json
import os
import shutil
from typing import Any, Dict

import jinja2
import loguru

try:
    # for python 3.9+
    BASE_TEMPLATES_DIRECTORY = importlib.resources.files("hamilton_sdk.cli.templates")
except AttributeError:
    # for python <3.9
    import pkg_resources

    BASE_TEMPLATES_DIRECTORY = pkg_resources.resource_filename("hamilton_sdk.cli.templates", "")

logger = loguru.logger

HAMILTON_DIR_LOCATION = "components"
CONFIG_DIR_LOCATION = "config"
DATA_DIR_LOCATION = "data"

TEMPLATE_FILES = [
    "run.py.jinja2",
    "requirements.txt.jinja2",
    "README.md.jinja2",
    ".env.jinja2",
]

EXECUTABLE_TEMPLATE_FILES = ["run.sh.jinja2"]


TEMPLATES = [
    "hello_world",
    "machine_learning",
    "time_series_feature_engineering",
    "data_processing",
]


def print_out_next_steps(location: str, template: str):
    print("...")


def fill_and_copy_template(
    template_data: Dict[str, Any], template_location: str, template_dest: str, executable: bool
):
    environment = jinja2.Environment()
    with open(template_location) as f:
        template = environment.from_string(f.read())
        template_rendered = template.render(**template_data, undefined=jinja2.StrictUndefined)
    with open(template_dest, "w") as template_write_file:
        template_write_file.write(template_rendered)
    if executable:
        os.chmod(template_dest, 0o777)


def fill_and_copy_templates(
    common_template_location: str,
    copy_location: str,
    username: str,
    api_key: str,
    project_id: int,
    template_name: str,
    template_data_file: str,
):
    with open(template_data_file) as f:
        template_data = json.load(f)
    template_args = {
        **template_data,
        "username": username,
        "api_key": api_key,
        "project_id": project_id,
        "template_name": template_name,
    }
    executable = [False] * len(TEMPLATE_FILES) + [True] * len(EXECUTABLE_TEMPLATE_FILES)
    for executable, template_file in zip(executable, TEMPLATE_FILES + EXECUTABLE_TEMPLATE_FILES):
        fill_and_copy_template(
            template_args,
            os.path.join(common_template_location, template_file),
            os.path.join(copy_location, template_file.replace(".jinja2", "")),
            executable=executable,
        )


def copy_static_files(template_location: str, copy_location: str):
    """Copies over static template files to the desired location.

    :param template_location:
    :param copy_location:
    :return:
    """

    # TODO -- copy over pipeline directory
    # TODO -- copy over data directory
    # TODO -- copy over .env (static for now)
    # TODO -- copy over run.sh (static for now)
    for dir_to_copy in [HAMILTON_DIR_LOCATION, CONFIG_DIR_LOCATION, DATA_DIR_LOCATION]:
        source = os.path.join(template_location, dir_to_copy)
        destination = os.path.join(copy_location, dir_to_copy)
        logger.debug(f"Copying over {source} to {destination}")
        # Only copy over if the source already exists
        if os.path.exists(source):
            shutil.copytree(source, destination)


def generate_template(
    username: str,
    api_key: str,
    project_id: int,
    template: str,
    copy_to_location: str,
    template_locations: str = BASE_TEMPLATES_DIRECTORY,
):
    f"""Generates the directory structure + enough to get started for the project.
    This is a project with:
    - {HAMILTON_DIR_LOCATION}/
        - README.md
        - file_1.py
        - file_2.py
        - ...
    - {CONFIG_DIR_LOCATION}/ (optional)
        - README.md
        - [config.py]
    - {DATA_DIR_LOCATION}/ (optional, if the project needs it)
    - run.py (entrypoint -- dagworks + pure hamilton)
    - requirements.txt
    - README.md
    - .env # environment variable with the right information
    - run.sh # bash script to set env/run run.py

    """
    if os.path.exists(copy_to_location):
        raise ValueError(
            f"Directory {copy_to_location} already exists. Please delete it "
            f"or choose another location."
        )
    os.mkdir(copy_to_location)
    logger.info(
        f"Initializing project {project_id} for user {username} "
        f"with template {template} at location {template_locations}."
    )
    template_location = os.path.join(template_locations, template)
    common_location = os.path.join(template_locations, "common")
    # Copy static files over from the template-specific location
    copy_static_files(template_location, copy_to_location)
    logger.info("Copying over files...")
    template_data_file = os.path.join(template_location, "template_data.json")
    # Fill and copy templates from common locations
    fill_and_copy_templates(
        common_template_location=common_location,
        copy_location=copy_to_location,
        username=username,
        api_key=api_key,
        project_id=project_id,
        template_name=template,
        template_data_file=template_data_file,
    )
    print_out_next_steps(copy_to_location, template)
    logger.info("Done!")
    logger.info(
        "Your next steps are:\n"
        "(1) [Optional] Commit this code to a git repository and push it to origin.\n"
        "(2) Create your python virtual environment and install the dependencies "
        "you need to run the code.\n"
        "For example if using pip, do `pip install -r requirements.txt`.\n"
        "(3) Execute `./run.sh` to run the example."
    )
