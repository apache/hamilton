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
The code  is an example utility script that you could write
to help you interface with Hamilton and its lineage capabilities.
"""

from typing import Dict, List

import data_loading
import features
import model_pipeline
import sets
from sklearn import base as sk_base

from hamilton import base, driver


def create_titanic_DAG_driver():
    """Creates a Driver object for the Titanic DAG."""
    config = {}  # Empty for this example.
    adapter = base.DefaultAdapter()
    dr = driver.Driver(config, data_loading, features, sets, model_pipeline, adapter=adapter)
    return dr


def get_git_sha():
    """Returns the git sha of the current repository."""
    import git

    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha
    return sha


def create_rf_model(titanic_dag_driver: driver.Driver, path_for_image: str):
    """Creates the random forest model & encoders by executing the titanic DAG

    :param dr:
    :param path_for_image:
    :return: the result of the execution and the git sha of the current repository.
    """
    sha = get_git_sha()
    inputs = {
        "location": "data/train.csv",
        "index_col": "passengerid",
        "target_col": "survived",
        "random_state": 42,
        "max_depth": None,
        "validation_size_fraction": 0.33,
    }
    result = titanic_dag_driver.execute(
        [model_pipeline.fit_random_forest, features.encoders], inputs=inputs
    )
    titanic_dag_driver.visualize_execution(
        [model_pipeline.fit_random_forest, features.encoders],
        path_for_image,
        {"format": "png"},
        inputs=inputs,
    )
    return {"result": result, "sha": sha}


def visualize_downstream(dr: driver.Driver, start_node: str, image_path: str) -> None:
    """Visualizes the downstream nodes of the start_node.

    :param dr: the driver to query.
    :param start_node: the node to start the visualization from.
    :param image_path: path to save the image to.
    """
    dr.display_downstream_of(
        start_node, output_file_path=image_path, render_kwargs={"format": "png"}, graphviz_kwargs={}
    )


def visualize_upstream(dr: driver.Driver, end_node: str, image_path: str) -> None:
    """Visualizes the downstream nodes of the start_node.

    :param dr: the driver to query.
    :param end_node: the node to go backwards in the visualization from.
    :param image_path: path to save the image to.
    """
    dr.display_upstream_of(
        end_node, output_file_path=image_path, render_kwargs={"format": "png"}, graphviz_kwargs={}
    )


def what_source_data_teams_are_upstream(dr: driver.Driver, output_name: str) -> List[dict]:
    """Function to return a list of teams that own the source data that is upstream of the output_name.

    :param dr: the driver object to use to query.
    :param output_name: the name of the output node to query.
    :return: List of dictionaries with the team, function, and source.
    """
    nodes = dr.what_is_upstream_of(output_name)
    teams = []
    for node in nodes:
        if node.tags.get("source"):
            teams.append(
                {
                    "team": node.tags.get("owner"),
                    "function": node.name,
                    "source": node.tags.get("source"),
                }
            )
    return teams


def what_pii_is_used_where(dr: driver.Driver) -> Dict[str, List[dict]]:
    """Function to return a dictionary of PII to artifacts that consume that PII directly or indirectly.

    :param dr: the driver object
    :return: a dictionary of PII to artifacts that consume that PII.
    """
    pii_nodes = [n for n in dr.list_available_variables() if n.tags.get("PII") == "true"]
    pii_to_artifacts = {}
    for node in pii_nodes:
        pii_to_artifacts[node.name] = []
        downstream_nodes = dr.what_is_downstream_of(node.name)
        for dwn_node in downstream_nodes:
            if dwn_node.tags.get("artifact"):
                pii_to_artifacts[node.name].append(
                    {
                        "team": dwn_node.tags.get("owner", "unknown"),
                        "function": dwn_node.name,
                        "artifact": dwn_node.tags.get("artifact"),
                    }
                )
    return pii_to_artifacts


def what_artifacts_are_downstream(dr: driver.Driver, source_name: str) -> List[dict]:
    """Function to return a list of artifacts that are downstream of a given source.

    :param dr: driver object to query.
    :param source_name: the node to start the query from.
    :return: List of dictionaries with the team, function, and artifact.
    """
    nodes = dr.what_is_downstream_of(source_name)
    artifacts = []
    for node in nodes:
        if node.tags.get("artifact"):
            artifacts.append(
                {
                    "team": node.tags.get("owner", "FIX_ME"),
                    "function": node.name,
                    "artifact": node.tags.get("artifact"),
                }
            )
    return artifacts


def what_classifiers_are_downstream(dr: driver.Driver, start_node: str) -> List[dict]:
    """Shows that you can also filter nodes based on output type.

    :param dr: driver object to query.
    :param start_node: the node to start the query from.
    :return: List of dictionaries with the team, function, and importance.
    """
    nodes = dr.what_is_downstream_of(start_node)
    models = []
    for node in nodes:
        if node.type == sk_base.ClassifierMixin:
            models.append(
                {
                    "team": node.tags.get("owner"),
                    "function": node.name,
                    "importance": node.tags.get("importance"),
                }
            )
    return models


def what_nodes_are_on_path_between(dr: driver.Driver, start_node: str, end_node: str) -> List[dict]:
    """Function that returns the nodes that are on the path between two nodes.

    :param dr: driver object to query.
    :param start_node: the node to start the query from.
    :param end_node: the node to end the query at.
    :return: List of dictionaries with the team, function, importance, and node type.
    """
    nodes = dr.what_is_the_path_between(start_node, end_node)
    node_info = []
    for node in nodes:
        node_info.append(
            {
                "team": node.tags.get("owner"),
                "function": node.name,
                "importance": node.tags.get("importance"),
                "type": node.type,
            }
        )
    return node_info


if __name__ == "__main__":
    # you'd more likely use `click()` in real life.
    import pprint
    import sys

    usage_string = (
        "Usage is python lineage_commands.py [create_model IMAGE_PATH |\n"
        "                                     upstream VALUE |\n"
        "                                     downstream VALUE |\n"
        "                                     path START_NODE END_NODE |\n"
        "                                     PII |\n"
        "                                     visualize [upstream|downstream] VALUE IMAGE_PATH]\n"
    )
    if len(sys.argv) < 2:
        print(usage_string)
        sys.exit(1)
    command = sys.argv[1]
    _driver = create_titanic_DAG_driver()
    if command == "create_model":
        if len(sys.argv) < 3:
            pprint.pprint("Usage is python lineage_commands.py create_model IMAGE_PATH")
            sys.exit(1)
        image_path = sys.argv[2]
        _result = create_rf_model(_driver, image_path)
        pprint.pprint(_result)
        # TODO: serialize -- send onwards
    elif command == "PII":
        _result = what_pii_is_used_where(_driver)
        pprint.pprint(_result)
    elif command == "upstream":
        name = sys.argv[2]
        _upstream = what_source_data_teams_are_upstream(_driver, name)
        pprint.pprint(_upstream)
    elif command == "downstream":
        name = sys.argv[2]
        _downstream = what_artifacts_are_downstream(_driver, name)
        pprint.pprint(_downstream)
    elif command == "visualize":
        if len(sys.argv) < 5:
            pprint.pprint(
                "Usage is python lineage_commands.py visualize [upstream|downstream] VALUE IMAGE_PATH"
            )
            sys.exit(1)
        up_or_down = sys.argv[2]
        node_name = sys.argv[3]
        image_path = sys.argv[4]
        if up_or_down == "upstream":
            visualize_upstream(_driver, node_name, image_path)
        else:
            visualize_downstream(_driver, node_name, image_path)
    elif command == "path":
        if len(sys.argv) < 4:
            pprint.pprint("Usage is python lineage_commands.py path START_NODE END_NODE")
            sys.exit(1)
        start_node = sys.argv[2]
        end_node = sys.argv[3]
        _path = what_nodes_are_on_path_between(_driver, start_node, end_node)
        pprint.pprint(_path)
    else:
        print(f"No such command {command}.\n{usage_string}")
