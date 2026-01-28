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

import uuid
from typing import Any

import pytest
from django.test import AsyncClient
from trackingserver_auth.models import User
from trackingserver_projects.schema import ProjectIn, ProjectUpdate, Visibility


async def _setup_sample_project(
    async_client: AsyncClient, username
) -> tuple[int, str, dict[str, Any]]:
    user_loaded = await User.objects.aget(email=username)
    project_name = str(uuid.uuid4())
    project_to_create = ProjectIn(
        name=project_name,
        description="test project",
        tags={"key": "value"},
        visibility=Visibility(
            user_ids_visible=[],
            team_ids_visible=[],
            team_ids_writable=[],
            user_ids_writable=[user_loaded.id],
        ),
    )
    post_response = await async_client.post(
        "/api/v1/projects",
        data=project_to_create.model_dump(),
        content_type="application/json",
        headers={"test_username": username},
    )
    assert post_response.status_code == 200, post_response.content
    post_response_data = post_response.json()
    assert post_response_data["name"] == project_name
    assert post_response_data["description"] == "test project"
    assert post_response_data["tags"] == {"key": "value"}
    return post_response_data["id"], post_response_data["name"], post_response_data


@pytest.mark.asyncio
async def test_create_and_get_project(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    post_response_id, project_name, post_response_data = await _setup_sample_project(
        async_client, username
    )
    get_response = await async_client.get(
        f"/api/v1/projects/{post_response_id}", headers={"test_username": username}
    )
    assert get_response.status_code == 200, get_response.content
    get_response_data = get_response.json()
    assert get_response_data["name"] == project_name
    assert get_response_data["description"] == "test project"
    assert get_response_data["tags"] == {"key": "value"}
    assert get_response_data["id"] == post_response_id

    get_response = await async_client.get(
        f"/api/v1/projects/{post_response_id}", headers={"test_username": username}
    )
    assert get_response.status_code == 200, get_response.content
    get_response_data = get_response.json()
    assert get_response_data["name"] == project_name
    assert get_response_data["description"] == "test project"
    assert get_response_data["tags"] == {"key": "value"}
    assert get_response_data["id"] == post_response_id


@pytest.mark.asyncio
async def test_create_and_get_all_projects(async_client: AsyncClient, db):
    username = "user_individual@no_team.com"
    post_response_id, project_name, post_response_data = await _setup_sample_project(
        async_client, username
    )
    get_response = await async_client.get(
        "/api/v1/projects", headers={"test_username": username}, data={"offset": 0, "limit": 100}
    )
    ids_returned = [item["id"] for item in get_response.json()]
    assert post_response_id in ids_returned
    assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_create_then_update_project(async_client: AsyncClient, db):
    user_with_no_team = "user_individual@no_team.com"
    user_loaded = await User.objects.aget(email=user_with_no_team)
    user_to_share_with = "user_1_team_1@team1.com"
    user_to_share_with_loaded = await User.objects.aget(email=user_to_share_with)
    username = "user_individual@no_team.com"
    post_response_id, project_name, post_response_data = await _setup_sample_project(
        async_client, username
    )

    # Update the project
    # We're going to update description, tags, and visibility

    project_to_update = ProjectUpdate(
        description="new description",
        tags={"key": "new value"},
        visibility=Visibility(
            user_ids_visible=[user_to_share_with_loaded.id],
            team_ids_visible=[],
            user_ids_writable=[user_loaded.id],
            team_ids_writable=[],
        ),
    )

    put_response = await async_client.put(
        f"/api/v1/projects/{post_response_id}",
        data={"project": project_to_update.dict(exclude_unset=True)},
        content_type="application/json",
        headers={"test_username": user_with_no_team},
    )
    assert put_response.status_code == 200
    put_response_data = put_response.json()
    assert put_response_data["name"] == project_name
    assert put_response_data["description"] == project_to_update.description
    assert put_response_data["tags"] == project_to_update.tags
    assert put_response_data["id"] == post_response_id
    get_response = await async_client.get(
        f"/api/v1/projects/{post_response_id}", headers={"test_username": user_with_no_team}
    )
    assert get_response.status_code == 200
    get_response_data = get_response.json()
    assert get_response_data["name"] == project_name
    assert get_response_data["description"] == project_to_update.description
    assert get_response_data["tags"] == project_to_update.tags
    assert get_response_data["id"] == post_response_id
