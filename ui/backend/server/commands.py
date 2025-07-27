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

import configparser
import logging
import os
import sys
import threading
import time
import webbrowser
from contextlib import contextmanager
from enum import Enum
from typing import Optional

import requests
from django.core.management import execute_from_command_line

import hamilton_ui

logger = logging.getLogger(__name__)


@contextmanager
def extend_sys_path(path):
    original_sys_path = sys.path[:]
    try:
        sys.path.insert(0, path)
        yield
    finally:
        sys.path = original_sys_path


# Usage

# Perform operations that require importing modules from the specified path


@contextmanager
def set_env_variables(vars: dict):
    original_values = {}
    try:
        # Set new values and store original values
        for key, value in vars.items():
            original_values[key] = os.getenv(key)
            os.environ[key] = value
        yield
    finally:
        # Restore original values or delete if they were not set originally
        for key in vars:
            if original_values[key] is None:
                del os.environ[key]
            else:
                os.environ[key] = original_values[key]


def _open_when_ready(check_url: str, open_url: str):
    while True:
        try:
            response = requests.get(check_url)
            if response.status_code == 200:
                webbrowser.open(open_url)
                return
            else:
                pass
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.1)


class SettingsFile(str, Enum):
    mini = "server.settings_mini"
    deploy = "server.settings"


def _initialize_db_mini_mode(base_dir):
    if not os.path.exists(base_dir):
        try:
            os.makedirs(os.path.join(base_dir, "blobs"))
            os.makedirs(os.path.join(base_dir, "db"))
        except Exception as e:
            logger.exception(f"Error creating directories -- manually create them instead: {e}")


def _load_env(config_file: str):
    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option
    config.read(config_file)
    if "deploy" not in config:
        raise ValueError(
            f"Invalid config file: {config_file}. Must be an ini-format file with one section named 'deploy'"
        )
    return dict(config["deploy"])


def run(
    port: int,
    base_dir: str,
    no_migration: bool,
    no_open: bool,
    settings_file: str,
    config_file: Optional[str],
):
    if not hasattr(SettingsFile, settings_file):
        raise ValueError(f"Invalid settings file: {settings_file}")

    settings_file = SettingsFile[settings_file]

    if not no_open:
        thread = threading.Thread(
            target=_open_when_ready,
            kwargs={
                "open_url": (open_url := f"http://localhost:{port}"),
                "check_url": f"{open_url}/api/v0/health",
            },
            daemon=True,
        )
        thread.start()
    env = {
        "HAMILTON_BASE_DIR": base_dir,
    }

    with extend_sys_path(hamilton_ui.__path__[0]):
        # This is here as some folks didn't have it created automatically through django
        if settings_file == SettingsFile.mini:
            _initialize_db_mini_mode(base_dir)

        else:
            if config_file is None:
                raise ValueError(f"Must provide a config file for settings file: {settings_file}")
            env = {**_load_env(config_file), **env}
        with set_env_variables(env):
            settings_file_param = f"--settings={settings_file.value}"
            if not no_migration:
                execute_from_command_line(["manage.py", "migrate", settings_file_param])
            execute_from_command_line(
                # Why insecure? Because we're running locally using django's server which
                # is not specifically meant for production. That said, we'll be fixing this up shortly,
                # but for now, users who want to run this not in debug mode and serve it will want to use this:
                # See https://stackoverflow.com/questions/5836674/why-does-debug-false-setting-make-my-django-static-files-access-fail
                ["manage.py", "runserver", settings_file_param, f"0.0.0.0:{port}", "--insecure"]
            )
