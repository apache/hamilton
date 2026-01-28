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

import random
import string

import pytest
from django.test import AsyncClient
from django.utils.http import urlencode
from trackingserver_template.schema import (
    CodeArtifactIn,
    CodeLog,
    DAGTemplateIn,
    File,
    NodeTemplateIn,
)

from tests.test_lifecycle.test_projects import _setup_sample_project


def _generate_some_sample_nodes(
    n_nodes: int, n_code_artifacts: int
) -> tuple[list[NodeTemplateIn], list[CodeArtifactIn]]:
    nodes = []
    code_artifacts = []
    for i in range(n_nodes):
        nodes.append(
            NodeTemplateIn(
                name=f"node_{i}",
                dependencies=[] if i == 0 else [f"node_{i - 1}"],
                dependency_specs=(
                    [] if i == 0 else [{"type": "int"}]
                ),  # TODO -- model this with actual dependency specs
                dependency_specs_type="python_type_for_testing",
                dependency_specs_schema_version=1,
                output={"type": "int"},
                output_type="python_type_for_testing",
                output_schema_version=1,
                documentation="Documentation for Node",
                tags={"node_name": f"node_{i}"},
                code_pointer="code_artifact_1",
                classifications=["transform"],
                code_artifact_pointers=[
                    f"code_artifact_{i % n_code_artifacts}, code_artifact_{(i + 1) % n_code_artifacts}"
                ],
            )
        )
    for i in range(n_code_artifacts):
        code_artifacts.append(
            CodeArtifactIn(
                name=f"code_artifact_{i}",
                type="p_function",
                path="path/to/code",
                start=10 * i,
                end=10 * i + 5,
                url="",
            )
        )
    return nodes, code_artifacts


def _generate_sample_dag_template(
    nodes: list[NodeTemplateIn], code_artifacts: list[CodeArtifactIn]
) -> DAGTemplateIn:
    return DAGTemplateIn(
        name="sample_dag_template",
        template_type="HAMILTON",
        config={"config_key": "config_value"},
        # Random one for now
        dag_hash="".join(random.choices(string.ascii_letters + string.digits, k=64)),
        nodes=nodes,
        code_artifacts=code_artifacts,
        code_log=CodeLog(files=[File(path="path/to/file", contents="file contents")]),
        code_version_info_type="git",
        code_version_info={
            "git_hash": "git_hash_1",
            "git_repo": "dagworks-inc/hamilton",
            "git_branch": "main",
            "committed": True,
        },
        code_version_info_schema=1,
        code_hash="".join(random.choices(string.ascii_letters + string.digits, k=64)),
        tags={"dag_template_name": "sample_dag_template"},
    )


@pytest.mark.asyncio
async def test_create_and_get_dag_template(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    dag_template_to_generate = _generate_sample_dag_template(*_generate_some_sample_nodes(10, 3))
    project_id, *_ = await _setup_sample_project(async_client, username)
    post_dag_template_response = await async_client.post(
        f"/api/v1/dag_templates?{urlencode({'project_id': project_id})}",
        data=dag_template_to_generate.model_dump(),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert post_dag_template_response.status_code == 200, post_dag_template_response.content
    dag_template_id = post_dag_template_response.json()["id"]
    get_dag_template_response = await async_client.get(
        f"/api/v1/dag_templates/{dag_template_id}", headers={"test_username": username}
    )
    assert get_dag_template_response.status_code == 200, get_dag_template_response.content
    (dag_template,) = get_dag_template_response.json()
    assert dag_template["name"] == dag_template_to_generate.name
    assert len(dag_template["nodes"]) == len(dag_template_to_generate.nodes)
    assert dag_template["nodes"][-1]["name"] == dag_template_to_generate.nodes[-1].name
    assert dag_template["id"] == dag_template_id
    assert dag_template["template_type"] == dag_template_to_generate.template_type
    assert len(dag_template["code_artifacts"]) == len(dag_template_to_generate.code_artifacts)
    return dag_template_id, username, project_id


@pytest.mark.asyncio
async def test_archive_dag_template(async_client: AsyncClient, db):
    # Lazy -- using the test above
    # Could put it in a helper, but this is the only one that uses it
    dag_template_id, username, project_id = await test_create_and_get_dag_template(async_client, db)
    get_dag_template_response = await async_client.put(
        f"/api/v1/update_dag_templates/{dag_template_id}",
        headers={"test_username": username},
        content_type="application/json",
        data={"is_active": False},
    )
    assert get_dag_template_response.status_code == 200, get_dag_template_response.content
    get_dag_template_response = await async_client.get(
        f"/api/v1/dag_templates/{dag_template_id}", headers={"test_username": username}
    )
    # no DAG template, archived
    assert get_dag_template_response.status_code == 404, get_dag_template_response.content


@pytest.mark.asyncio
async def test_create_and_get_all_project_dag_templates(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    project_id, *_ = await _setup_sample_project(async_client, username)
    num_dag_templates = 4
    dag_templates_created = []
    for _i in range(num_dag_templates):
        dag_template_to_generate = _generate_sample_dag_template(
            *_generate_some_sample_nodes(10, 5)
        )
        post_dag_template_response = await async_client.post(
            f"/api/v1/dag_templates?{urlencode({'project_id': project_id})}",
            data=dag_template_to_generate.model_dump(),
            content_type="application/json",
            headers={"test_username": username},
        )
        assert post_dag_template_response.status_code == 200, post_dag_template_response.content
        dag_templates_created.append(post_dag_template_response.json()["id"])
    get_dag_templates_response = await async_client.get(
        f"/api/v1/dag_templates/latest/?{urlencode({'project_id': project_id, 'limit': num_dag_templates})}",
        headers={"test_username": username},
    )
    assert get_dag_templates_response.status_code == 200, get_dag_templates_response.content
    dag_templates = get_dag_templates_response.json()
    assert len(dag_templates) == num_dag_templates
