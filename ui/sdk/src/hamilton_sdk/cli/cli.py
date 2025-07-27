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

import click
from hamilton_sdk.cli import initialize


@click.group()
def cli():
    pass


@click.command()
@click.option("--api-key", "-k", required=True, type=str)
@click.option("--username", "-u", required=True, type=str)
@click.option("--project-id", "-p", required=True, type=int)
@click.option("--template", "-t", required=False, type=click.Choice(initialize.TEMPLATES))
@click.option("--location", "-l", type=click.Path(exists=False, dir_okay=True), default=None)
def init(api_key: str, username: str, project_id: int, template: str, location: str):
    if location is None:
        # If location is none we default to, say, ./hello_world
        location = os.path.join(os.getcwd(), template)
    initialize.generate_template(
        username=username,
        api_key=api_key,
        project_id=project_id,
        template=template,
        copy_to_location=location,
    )


cli.add_command(init)

if __name__ == "__main__":
    cli()
