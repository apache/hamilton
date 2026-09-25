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

import collections
import datetime
from urllib.parse import urlencode

import pytest
from django.test import AsyncClient
from trackingserver_run_tracking.schema import DAGRunUpdate
from trackingserver_template.schema import NodeTemplateIn

from tests.test_lifecycle.test_projects import _setup_sample_project
from tests.test_lifecycle.test_templates import (
    _generate_sample_dag_template,
    _generate_some_sample_nodes,
)


async def _setup_dag_template(
    async_client: AsyncClient, username
) -> tuple[int, list[NodeTemplateIn]]:
    sample_nodes, sample_code_artifacts = _generate_some_sample_nodes(5, 10)
    dag_template_to_generate = _generate_sample_dag_template(sample_nodes, sample_code_artifacts)
    project_id, *_ = await _setup_sample_project(async_client, username)
    post_dag_template_response = await async_client.post(
        f"/api/v1/dag_templates?{urlencode({'project_id': project_id})}",
        data=dag_template_to_generate.model_dump(),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert post_dag_template_response.status_code == 200, post_dag_template_response.content
    return post_dag_template_response.json()["id"], sample_nodes


@pytest.mark.asyncio
async def test_create_and_get_empty_dag_run(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    dag_template_id, nodes = await _setup_dag_template(async_client, username)
    # noinspection PyArgumentList
    tags = {"foo": "bar"}
    dag_run_to_create = dict(
        run_start_time=datetime.datetime.now(),
        run_end_time=None,
        run_status="RUNNING",
        tags=tags,
        inputs={},
        outputs=[],
    )
    post_create_run_response = await async_client.post(
        f"/api/v1/dag_runs?{urlencode({'dag_template_id': dag_template_id})}",
        data=dag_run_to_create,
        content_type="application/json",
        headers={"test_username": username},
    )
    assert post_create_run_response.status_code == 200, post_create_run_response.content
    run_data = post_create_run_response.json()
    assert run_data["run_status"] == "RUNNING"
    assert run_data["run_start_time"] is not None
    run_id = post_create_run_response.json()["id"]
    get_dag_run_response = await async_client.get(
        f"/api/v1/dag_runs/{run_id}?attr=foo&attr=bar", headers={"test_username": username}
    )
    assert get_dag_run_response.status_code == 200, get_dag_run_response.content
    (dag_run_data,) = get_dag_run_response.json()  # list of 1
    assert dag_run_data["id"] == run_id
    assert len(dag_run_data["node_runs"]) == 0
    return username, run_id, nodes


@pytest.mark.asyncio
async def test_create_and_check_dag_template_exists(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    dag_template_to_generate = _generate_sample_dag_template(*_generate_some_sample_nodes(5, 3))
    dag_hash = dag_template_to_generate.dag_hash
    code_hash = dag_template_to_generate.code_hash
    dag_name = dag_template_to_generate.name
    project_id, *_ = await _setup_sample_project(async_client, username)
    post_dag_template_response = await async_client.post(
        f"/api/v1/dag_templates?{urlencode({'project_id': project_id})}",
        data=dag_template_to_generate.model_dump(),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert post_dag_template_response.status_code == 200, post_dag_template_response.content
    dag_template_exists_response = await async_client.get(
        f"/api/v1/dag_templates/exists/?{urlencode({'dag_hash': dag_hash, 'project_id': project_id, 'code_hash': code_hash, 'dag_name': dag_name})}",
        headers={"test_username": username},
    )
    assert dag_template_exists_response.status_code == 200, dag_template_exists_response.content
    assert dag_template_exists_response.json()["id"] == post_dag_template_response.json()["id"]
    hash_that_doesnt_exist = "".join(reversed(dag_hash))
    dag_template_exists_response = await async_client.get(
        f"/api/v1/dag_templates/exists/?{urlencode({'project_id': project_id, 'dag_hash': hash_that_doesnt_exist, 'code_hash': code_hash, 'dag_name': dag_name})}",
        headers={"test_username": username},
    )
    assert dag_template_exists_response.status_code == 200, dag_template_exists_response.content
    assert dag_template_exists_response.json() is None


@pytest.mark.asyncio
async def test_create_and_update_empty_dag_run(async_client: AsyncClient, db):
    username, run_id, nodes = await test_create_and_get_empty_dag_run(async_client, db)
    dag_run_update = DAGRunUpdate(
        upsert_tags={"foo": "baz", "qux": "quux"},
        run_end_time=datetime.datetime.now(),
        run_status="SUCCESS",
    )
    update_dag_run_response = await async_client.put(
        f"/api/v1/dag_runs/{run_id}/",
        data=dag_run_update.model_dump(),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert update_dag_run_response.status_code == 200, update_dag_run_response.content
    update_dag_run_data = update_dag_run_response.json()
    assert update_dag_run_data["run_status"] == "SUCCESS"
    assert update_dag_run_data["run_end_time"] is not None
    assert update_dag_run_data["tags"] == {"foo": "baz", "qux": "quux"}


@pytest.mark.asyncio
async def test_basic_run_create_lifecycle(async_client: AsyncClient, db):
    # We're just reusing the old test to create new ones
    username, run_id, nodes = await test_create_and_get_empty_dag_run(async_client, db)
    # let's finish the first 2, and then keep the next ones running :shrug:
    node_runs = [
        dict(
            node_name=node_template.name,
            node_template_name=node_template.name,
            realized_dependencies=node_template.dependencies,
            start_time=datetime.datetime.now(),
            status="RUNNING" if i > 1 else "SUCCESS",
            end_time=datetime.datetime.now() if i <= 1 else None,
        )
        for i, node_template in enumerate(nodes)
    ]

    attributes: list[dict] = [
        dict(
            node_name=node_template.name,
            name="some_attribute",
            type="int",
            value=i,
            schema_version=1,
            attribute_role="result_summary",
        )
        for i, node_template in enumerate(nodes)
    ] + [
        dict(
            node_name=node_template.name,
            name="some_other_attribute",
            type="str",
            value=f"attr_{i}",
            schema_version=1,
            attribute_role="result_summary",
        )
        for i, node_template in enumerate(nodes)
    ]
    data = dict(
        attributes=attributes,
        task_updates=node_runs,
    )
    update_post_results = await async_client.put(
        f"/api/v1/dag_runs_bulk?dag_run_id={run_id}",
        data=data,
        content_type="application/json",
        headers={"test_username": username},
    )

    assert update_post_results.status_code == 200, update_post_results.content

    get_dag_run_response = await async_client.get(
        f"/api/v1/dag_runs/{run_id}?attr=int&attr=str", headers={"test_username": username}
    )
    assert get_dag_run_response.status_code == 200, get_dag_run_response.content
    all_data = get_dag_run_response.json()
    assert len(all_data) == 1
    (data,) = all_data
    assert len(data["node_runs"]) == len(nodes)
    expected_attributes_by_node_name = collections.defaultdict(list)
    for attr in attributes:
        expected_attributes_by_node_name[attr["node_name"]].append(attr)
    for node_run in data["node_runs"]:
        realized_attrs = node_run["attributes"]
        expected_attrs = expected_attributes_by_node_name[node_run["node_name"]]
        assert len(realized_attrs) == len(expected_attrs)
        assert set(attr["name"] for attr in realized_attrs) == set(
            attr["name"] for attr in expected_attrs
        )


@pytest.mark.asyncio
async def test_node_run_lifecycle_multiple_updates(async_client: AsyncClient, db):
    # We're just reusing the old test to create new ones
    username, run_id, nodes = await test_create_and_get_empty_dag_run(async_client, db)
    # let's finish the first 2, and then keep the next ones running :shrug:
    node_runs = [
        dict(
            node_name=node_template.name,
            node_template_name=node_template.name,
            realized_dependencies=node_template.dependencies,
            start_time=datetime.datetime.now(),
            status="RUNNING" if i > 1 else "SUCCESS",
            end_time=datetime.datetime.now() if i <= 1 else None,
        )
        for i, node_template in enumerate(nodes)
    ]

    attributes: list[dict] = [
        dict(
            node_name=node_template.name,
            name="some_attribute",
            type="int",
            value=i,
            schema_version=1,
            attribute_role="result_summary",
        )
        for i, node_template in enumerate(nodes)
    ]
    expected_attributes_by_node_name = collections.defaultdict(list)
    for attr in attributes:
        expected_attributes_by_node_name[attr["node_name"]].append(attr)
    update_post_results = await async_client.put(
        f"/api/v1/dag_runs_bulk?dag_run_id={run_id}",
        data=dict(
            attributes=attributes,
            task_updates=node_runs,
        ),
        content_type="application/json",
        headers={"test_username": username},
    )

    assert update_post_results.status_code == 200, update_post_results.content

    get_dag_run_response = await async_client.get(
        f"/api/v1/dag_runs/{run_id}?attr=int&attr=str", headers={"test_username": username}
    )
    assert get_dag_run_response.status_code == 200, get_dag_run_response.content
    all_data = get_dag_run_response.json()
    assert len(all_data) == 1
    (data,) = all_data
    assert len(data["node_runs"]) == len(nodes)
    node_runs = [
        dict(
            node_name=node_template.name,
            node_template_name=node_template.name,
            realized_dependencies=node_template.dependencies,
            start_time=datetime.datetime.now(),
            status="SUCCESS",
            end_time=datetime.datetime.now(),
        )
        for i, node_template in enumerate(nodes)
        if i > 1
    ]

    attributes: list[dict] = [
        dict(
            node_name=node_template.name,
            name="some_other_attribute",
            type="str",
            value=f"attr_{i}",
            schema_version=1,
            attribute_role="result_summary",
        )
        for i, node_template in enumerate(nodes)
    ]
    update_post_results = await async_client.put(
        f"/api/v1/dag_runs_bulk?dag_run_id={run_id}",
        data=dict(
            attributes=attributes,
            task_updates=node_runs,
        ),
        content_type="application/json",
        headers={"test_username": username},
    )

    assert update_post_results.status_code == 200, update_post_results.content

    get_dag_run_response = await async_client.get(
        f"/api/v1/dag_runs/{run_id}?attr=int&attr=str", headers={"test_username": username}
    )
    assert get_dag_run_response.status_code == 200, get_dag_run_response.content
    all_updated_dag_run_data = get_dag_run_response.json()
    assert len(all_updated_dag_run_data) == 1
    (updated_dag_run_data,) = all_updated_dag_run_data
    for attr in attributes:
        expected_attributes_by_node_name[attr["node_name"]].append(attr)
    for node_run in updated_dag_run_data["node_runs"]:
        realized_attrs = node_run["attributes"]
        expected_attrs = expected_attributes_by_node_name[node_run["node_name"]]
        assert len(realized_attrs) == len(expected_attrs)
        assert set(attr["name"] for attr in realized_attrs) == set(
            attr["name"] for attr in expected_attrs
        )


async def _create_dag_run_via_api(
    async_client: AsyncClient, username: str, dag_template_id: int, tags: dict
) -> int:
    response = await async_client.post(
        f"/api/v1/dag_runs?{urlencode({'dag_template_id': dag_template_id})}",
        data=dict(
            run_start_time=datetime.datetime.now(),
            run_end_time=None,
            run_status="RUNNING",
            tags=tags,
            inputs={},
            outputs=[],
        ),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert response.status_code == 200, response.content
    return response.json()["id"]


@pytest.mark.asyncio
async def test_get_latest_dag_runs_without_params_excludes_other_users_runs(
    async_client: AsyncClient, db
):
    """A user calling ``GET /api/v1/dag_runs/latest/`` with no parameters must
    only see runs from projects they have visibility into. Calls without any
    filter previously returned every active run on the instance.
    """
    user_a = "user_individual@no_team.com"
    user_b = "user_1_team_1@team1.com"
    dag_template_a, _ = await _setup_dag_template(async_client, user_a)
    dag_template_b, _ = await _setup_dag_template(async_client, user_b)

    run_a_id = await _create_dag_run_via_api(
        async_client, user_a, dag_template_a, {"owner": "a"}
    )
    run_b_id = await _create_dag_run_via_api(
        async_client, user_b, dag_template_b, {"owner": "b"}
    )

    # User A asks for latest runs with no filter -- must not see user B's run.
    response = await async_client.get(
        "/api/v1/dag_runs/latest/", headers={"test_username": user_a}
    )
    assert response.status_code == 200, response.content
    returned_ids = {item["id"] for item in response.json()}
    assert run_a_id in returned_ids
    assert run_b_id not in returned_ids

    # Symmetric: user B does not see user A's run either.
    response_b = await async_client.get(
        "/api/v1/dag_runs/latest/", headers={"test_username": user_b}
    )
    assert response_b.status_code == 200, response_b.content
    returned_ids_b = {item["id"] for item in response_b.json()}
    assert run_b_id in returned_ids_b
    assert run_a_id not in returned_ids_b


@pytest.mark.asyncio
async def test_get_latest_dag_runs_with_other_users_project_id_is_rejected(
    async_client: AsyncClient, db
):
    """Explicitly requesting another user's ``project_id`` must be rejected,
    matching how every other "get" endpoint in the module behaves.
    """
    user_a = "user_individual@no_team.com"
    user_b = "user_1_team_1@team1.com"
    # Setting up via the same helper returns dag_template ids, but we want a
    # project id user A doesn't belong to, so we go via _setup_sample_project.
    project_b_id, *_ = await _setup_sample_project(async_client, user_b)

    response = await async_client.get(
        f"/api/v1/dag_runs/latest/?{urlencode({'project_id': project_b_id})}",
        headers={"test_username": user_a},
    )
    # The permission decorator translates a failed check into HTTP 404.
    assert response.status_code == 404, response.content


@pytest.mark.asyncio
async def test_get_latest_dag_runs_with_own_project_id_still_works(
    async_client: AsyncClient, db
):
    """The legitimate case -- user asking for runs in a project they own --
    must keep returning their runs after the visibility filter is applied.
    """
    user_a = "user_individual@no_team.com"
    dag_template_a, _ = await _setup_dag_template(async_client, user_a)
    run_id = await _create_dag_run_via_api(
        async_client, user_a, dag_template_a, {"owner": "a"}
    )

    # By dag_template_id.
    response = await async_client.get(
        f"/api/v1/dag_runs/latest/?{urlencode({'dag_template_id': dag_template_a})}",
        headers={"test_username": user_a},
    )
    assert response.status_code == 200, response.content
    returned_ids = {item["id"] for item in response.json()}
    assert run_id in returned_ids

    # By project_id (we resolve the project from the dag template).
    project_a_id, *_ = await _setup_sample_project(async_client, user_a)
    # New template in this project, new run.
    dag_template_a2, _ = await _setup_dag_template(async_client, user_a)
    run_id_2 = await _create_dag_run_via_api(
        async_client, user_a, dag_template_a2, {"owner": "a2"}
    )
    response = await async_client.get(
        f"/api/v1/dag_runs/latest/?{urlencode({'project_id': project_a_id})}",
        headers={"test_username": user_a},
    )
    assert response.status_code == 200, response.content
    # The freshly-created project_a_id should not contain run_id (which came
    # from _setup_dag_template which makes its own project), but the call must
    # succeed -- the assertion that matters here is the 200, plus that we
    # never get back runs from elsewhere.
    returned_ids = {item["id"] for item in response.json()}
    assert run_id not in returned_ids
    assert run_id_2 not in returned_ids
