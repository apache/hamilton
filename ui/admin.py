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

import os
import shutil
import subprocess
import time
import webbrowser
from contextlib import contextmanager

import click
import requests
from loguru import logger


def _command(command: str, capture_output: bool) -> str:
    """Runs a simple command"""
    logger.info(f"Running command: {command}")
    if isinstance(command, str):
        command = command.split(" ")
        if capture_output:
            try:
                return (
                    subprocess.check_output(command, stderr=subprocess.PIPE, shell=False)
                    .decode()
                    .strip()
                )
            except subprocess.CalledProcessError as e:
                print(e.stdout.decode())
                print(e.stderr.decode())
                raise e
        subprocess.run(command, shell=False, check=True)


def _get_git_root() -> str:
    return _command("git rev-parse --show-toplevel", capture_output=True)


def open_when_ready(check_url: str, open_url: str):
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
        time.sleep(1)


@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


@click.group()
def cli():
    pass


def _build_ui(skip_install: bool = False):
    """
    Build the UI from source following Burr's pattern.

    Steps (matching burr/cli/__main__.py:135-156):
    1. npm install (unless --skip-install)
    2. npm run build
    3. rm -rf backend/server/build
    4. mkdir -p backend/server/build
    5. cp -a frontend/build/. backend/server/build/
    6. Verify critical files exist
    """
    # Step 1: Install dependencies (like Burr does)
    if not skip_install:
        logger.info("Installing npm dependencies...")
        cmd = "npm install --prefix ui/frontend"
        _command(cmd, capture_output=False)

    # Step 2: Build frontend
    logger.info("Building frontend...")
    cmd = "npm run build --prefix ui/frontend"
    _command(cmd, capture_output=False)

    # Step 3: Clear old build
    logger.info("Clearing old build directory...")
    cmd = "rm -rf ui/backend/server/build"
    _command(cmd, capture_output=False)

    # Step 4: Ensure directory exists
    cmd = "mkdir -p ui/backend/server/build"
    _command(cmd, capture_output=False)

    # Step 5: Copy with archive mode (like Burr: cp -a)
    logger.info("Copying built assets to backend...")
    cmd = "cp -a ui/frontend/build/. ui/backend/server/build/"
    _command(cmd, capture_output=False)

    # Step 6: Verify build succeeded
    git_root = _get_git_root()
    build_dir = os.path.join(git_root, "ui/backend/server/build")
    if not os.path.exists(os.path.join(build_dir, "index.html")):
        raise RuntimeError("Build failed: index.html not found in build directory")
    if not os.path.exists(os.path.join(build_dir, "static")):
        raise RuntimeError("Build failed: static/ directory not found in build directory")

    logger.info(f"✓ Build verified: {build_dir}")


@cli.command()
@click.option("--skip-install", is_flag=True, help="Skip npm install for faster builds")
def build_ui(skip_install: bool):
    logger.info("Building UI -- this may take a bit...")
    git_root = _get_git_root()
    with cd(git_root):
        _build_ui(skip_install=skip_install)
    logger.info("Built UI!")


@cli.command(help="Publishes the package to a repository")
@click.option("--prod", is_flag=True, help="Publish to pypi (rather than test pypi)")
@click.option("--no-wipe-dist", is_flag=True, help="Wipe the dist/ directory before building")
def build_and_publish(prod: bool, no_wipe_dist: bool):
    git_root = _get_git_root()
    install_path = os.path.join(git_root, "ui/backend")
    logger.info("Building UI -- this may take a bit...")
    build_ui.callback()  # use the underlying function, not click's object
    with cd(install_path):
        logger.info("Built UI!")
        if not no_wipe_dist:
            logger.info("Wiping dist/ directory for a clean publish.")
            shutil.rmtree("dist", ignore_errors=True)
        _command("python3 -m build", capture_output=False)
        repository = "pypi" if prod else "testpypi"
        _command(f"python3 -m twine upload --repository {repository} dist/*", capture_output=False)
        logger.info(f"Published to {repository}! 🎉")


if __name__ == "__main__":
    cli()
