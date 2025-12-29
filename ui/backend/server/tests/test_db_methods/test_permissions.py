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

import dataclasses
import datetime
import uuid
from typing import List, Tuple

import pytest
from trackingserver_auth.models import Team, User, UserTeamMembership
from trackingserver_base.auth.api_keys import create_api_key_for_user
from trackingserver_base.permissions.permissions import (
    user_can_create_api_key,
    user_can_create_project,
    user_can_delete_api_key,
    user_can_get_api_keys,
    user_can_get_dag_runs,
    user_can_get_dag_template,
    user_can_get_dag_templates,
    user_can_get_latest_dag_runs,
    user_can_get_project_by_id,
    user_can_get_projects,
    user_can_get_whoami,
    user_can_phone_home,
    user_can_update_project,
    user_can_write_to_dag_run,
    user_can_write_to_dag_template,
    user_can_write_to_project,
    user_project_visibility,
)
from trackingserver_projects.models import Project, ProjectTeamMembership, ProjectUserMembership
from trackingserver_projects.schema import ProjectIn, ProjectUpdate, Visibility
from trackingserver_run_tracking.models import DAGRun
from trackingserver_template.models import DAGTemplate


@dataclasses.dataclass
class MockRequest:
    auth: Tuple[User, List[Team]]


async def _get_authenticated_request(email: str) -> MockRequest:
    user = await User.objects.aget(email=email)
    teams = [
        item.team
        async for item in UserTeamMembership.objects.filter(user=user).prefetch_related("team")
    ]
    return MockRequest(auth=(user, teams))


@pytest.mark.asyncio
async def test_user_can_get_phone_home(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_phone_home(authenticated_request))[0] is True


@pytest.mark.asyncio
async def test_user_can_get_whoami(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_get_whoami(authenticated_request))[0] is True


@pytest.mark.asyncio
async def test_user_can_get_api_keys(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_get_api_keys(authenticated_request))[0] is True


@pytest.mark.asyncio
async def test_user_can_create_api_key(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_create_api_key(authenticated_request))[0] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user,allowed",
    [
        ("user_individual@no_team.com", True),
        ("user_with_no_permissions@no_one_invited_me.com", False),
    ],
)
async def test_user_can_delete_api_key(user: str, allowed: bool, db):
    authenticated_request = await _get_authenticated_request(user)
    user, _ = authenticated_request.auth
    user_creating_api_key = await User.objects.aget(email="user_individual@no_team.com")
    _, api_key_obj = await create_api_key_for_user(
        user_creating_api_key, key_name=str(uuid.uuid4())
    )
    assert (await user_can_delete_api_key(authenticated_request, api_key_id=api_key_obj.id))[
        0
    ] is allowed


# trackingserver_projects app permissions
@pytest.mark.asyncio
async def test_user_can_create_project_with_self_visibility(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    project = ProjectIn(
        name="test",
        description="test",
        tags={"foo": "bar"},
        visibility=Visibility(
            user_ids_visible=[user.id],
            user_ids_writable=[user.id],
            team_ids_visible=[],
            team_ids_writable=[],
        ),
    )
    assert (await user_can_create_project(authenticated_request, project))[0] is True


# trackingserver_projects app permissions
@pytest.mark.asyncio
async def test_user_can_create_project_with_team_visibility(db):
    authenticated_request = await _get_authenticated_request("user_1_team_1@team1.com")
    user, teams = authenticated_request.auth
    (team,) = teams
    project = ProjectIn(
        name="test",
        description="test",
        tags={"foo": "bar"},
        visibility=Visibility(
            user_ids_visible=[],
            user_ids_writable=[],
            team_ids_visible=[team.id],
            team_ids_writable=[team.id],
        ),
    )
    assert (await user_can_create_project(authenticated_request, project))[0] is True


@pytest.mark.asyncio
async def test_user_cannot_create_project_with_public_readability(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    public_team = await Team.objects.aget(name="Public")
    project = ProjectIn(
        name="test",
        description="test",
        tags={"foo": "bar"},
        visibility=Visibility(
            user_ids_visible=[user.id],
            user_ids_writable=[user.id],
            team_ids_visible=[public_team.id],
            team_ids_writable=[],
        ),
    )
    assert (await user_can_create_project(authenticated_request, project))[0] is False


@pytest.mark.asyncio
async def test_user_cannot_create_project_with_public_writability(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    public_team = await Team.objects.aget(name="Public")
    project = ProjectIn(
        name="test",
        description="test",
        tags={"foo": "bar"},
        visibility=Visibility(
            user_ids_visible=[user.id],
            user_ids_writable=[user.id],
            team_ids_visible=[],
            team_ids_writable=[public_team.id],
        ),
    )
    assert (await user_can_create_project(authenticated_request, project))[0] is False


@pytest.mark.asyncio
async def test_user_can_read_but_not_write_public_project(request, db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    project = await Project.objects.acreate(
        name="test",
        description="test",
        creator=user,  # This is not ideal as maybe the user should be able to create the project, but fine for now
        tags={},
    )
    public_team = await Team.objects.aget(name="Public")
    await ProjectTeamMembership.objects.acreate(
        project=project,
        team=public_team,
        role="read",
    )
    assert (await user_project_visibility(authenticated_request, project=project)) == "read"


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_has_visibility_when_granted_individual_access(role: str, db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    project = await Project.objects.acreate(name="test", description="test", creator=user, tags={})
    await ProjectUserMembership.objects.acreate(project=project, user=user, role=role)
    assert (await user_project_visibility(authenticated_request, project=project)) == role


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_does_not_have_visibility_when_not_granted_individual_access(role: str, db):
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    user_creating_project = await User.objects.aget(email="user_individual@no_team.com")
    project = await Project.objects.acreate(
        name="test", description="test", creator=user_creating_project, tags={}
    )
    # This is not necessary but we could see requirements on the db to ensure that
    # every project has *some* visibility
    await ProjectUserMembership.objects.acreate(
        project=project, user=user_creating_project, role=role
    )
    assert (await user_project_visibility(authenticated_request, project=project)) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_has_visibility_when_granted_team_access(role: str, db):
    authenticated_request = await _get_authenticated_request("user_1_team_1@team1.com")
    user, teams = authenticated_request.auth
    project = await Project.objects.acreate(name="test", description="test", creator=user, tags={})
    await ProjectTeamMembership.objects.acreate(project=project, team=teams[0], role=role)
    assert (await user_project_visibility(authenticated_request, project=project)) == role


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_does_not_have_visibility_when_not_granted_team_access(role: str, db):
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    user_creating_project = await User.objects.aget(email="user_1_team_1@team1.com")
    project = await Project.objects.acreate(
        name="test", description="test", creator=user_creating_project, tags={}
    )
    # This is not necessary but we could see requirements on the db to ensure that
    # every project has *some* visibility
    await ProjectTeamMembership.objects.acreate(
        project=project, team=await Team.objects.aget(name="Team 1"), role=role
    )
    assert (await user_project_visibility(authenticated_request, project=project)) is None


@pytest.mark.asyncio
async def test_user_cannot_get_project_by_id_does_not_exist(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_get_project_by_id(authenticated_request, project_id=999999999999))[
        0
    ] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_cannot_get_project_by_id_no_individual_access(role: str, db):
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    user_attempting_access, _ = authenticated_request.auth
    user_creating_project = await User.objects.aget(email="user_individual@no_team.com")
    project = await Project.objects.acreate(
        name="test", description="test", creator=user_creating_project, tags={}
    )
    await ProjectUserMembership.objects.acreate(
        project=project, user=user_creating_project, role=role
    )
    assert (await user_can_get_project_by_id(authenticated_request, project_id=project.id))[
        0
    ] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_cannot_get_project_by_id_no_team_access(role: str, db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user_attempting_access, _ = authenticated_request.auth
    user_creating_project = await User.objects.aget(email="user_1_team_1@team1.com")
    team = await Team.objects.aget(name="Team 1")
    project = await Project.objects.acreate(
        name="test", description="test", creator=user_creating_project, tags={}
    )
    await ProjectTeamMembership.objects.acreate(project=project, team=team, role=role)
    assert (await user_can_get_project_by_id(authenticated_request, project_id=project.id))[
        0
    ] is False


@pytest.mark.asyncio
async def test_user_cannot_update_project_that_does_not_exist(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (
        await user_can_update_project(
            authenticated_request, project_id=999999999999, project=ProjectUpdate()
        )
    )[0] is False


@pytest.mark.asyncio
async def test_user_cannot_update_project_with_read_access(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    user, _ = authenticated_request.auth
    project = await Project.objects.acreate(name="test", description="test", creator=user, tags={})
    await ProjectUserMembership.objects.acreate(project=project, user=user, role="read")
    assert (
        await user_can_update_project(
            authenticated_request, project=ProjectUpdate(), project_id=project.id
        )
    )[0] is False


@pytest.mark.asyncio
async def test_users_can_always_get_projects(db):
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    assert (await user_can_get_projects(authenticated_request))[0] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("role,allowed", [("read", False), ("write", True)])
async def test_user_can_edit_project_by_id_visibility_role(role: str, allowed: bool, db):
    authenticated_request = await _get_authenticated_request("user_1_team_1@team1.com")
    user, teams = authenticated_request.auth
    project = await Project.objects.acreate(name="test", description="test", creator=user, tags={})
    await ProjectTeamMembership.objects.acreate(project=project, team=teams[0], role=role)
    assert (await user_can_write_to_project(authenticated_request, project_id=project.id))[
        0
    ] is allowed
    return project, authenticated_request


@pytest.mark.asyncio
async def test_user_cannot_write_to_project_that_does_not_exist(db):
    authenticated_request = await _get_authenticated_request("user_1_team_1@team1.com")
    assert (await user_can_write_to_project(authenticated_request, project_id=999999999999))[
        0
    ] is False


# utility method for setting up projects for future testing
async def _setup_project_accessible_only_by(user_email: str, role: str) -> Tuple[Project, User]:
    user = await User.objects.aget(email=user_email)
    project = await Project.objects.acreate(name="test", description="test", creator=user, tags={})
    await ProjectUserMembership.objects.acreate(project=project, user=user, role=role)
    return project, user


@pytest.mark.asyncio
async def test_user_cannot_write_to_project_with_no_access(db):
    (
        project,
        user_creating_project,
    ) = await _setup_project_accessible_only_by("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_write_to_project(authenticated_request, project_id=project.id)
    assert can_do is False


async def _setup_project_and_dag_template(
    user_email: str, role: str
) -> Tuple[DAGTemplate, Project, User]:
    (
        project,
        user_creating_project,
    ) = await _setup_project_accessible_only_by(user_email, role)
    dag_template = await DAGTemplate.objects.acreate(
        project_id=project.id,
        name=str(uuid.uuid4()),
        template_type="HAMILTON",
        config={},
        dag_hash=str(uuid.uuid4()),
        is_active=True,
        tags={},
        code_hash=str(uuid.uuid4()),
        code_version_info_type="ad_hoc",
        code_version_info=None,
        code_version_info_schema=None,
        code_log_store="none",
        code_log_url=None,
        code_log_schema_version=1,
    )
    return dag_template, project, user_creating_project


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["read", "write"])
async def test_user_can_get_dag_template(db, role):
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    can_do, message = await user_can_get_dag_template(
        authenticated_request, dag_template_ids=str(dag_template.id)
    )
    assert can_do is True, message


@pytest.mark.asyncio
async def test_user_cannot_get_dag_template_with_no_access(db):
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_get_dag_template(
        authenticated_request, dag_template_ids=str(dag_template.id)
    )
    assert can_do is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role",
    [
        "read",
        "write",
    ],
)
async def test_user_can_get_dag_templates_with_access(db, role):
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    can_do, message = await user_can_get_dag_templates(authenticated_request, project_id=project.id)
    assert can_do is True, message


@pytest.mark.asyncio
async def test_user_cannot_get_dag_templates_with_no_access(db):
    (
        project,
        dag_template,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_get_dag_templates(authenticated_request, project_id=project.id)
    assert can_do is False


@pytest.mark.asyncio
@pytest.mark.parametrize("role,allowed", [("read", False), ("write", True)])
async def test_user_can_write_to_dag_template_with_access(db, role, allowed):
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    can_do, message = await user_can_write_to_dag_template(
        authenticated_request, dag_template_id=dag_template.id
    )
    assert can_do is allowed, message


@pytest.mark.asyncio
async def test_user_cannot_write_to_dag_template_with_no_access(db):
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_write_to_dag_template(
        authenticated_request, dag_template_id=dag_template.id
    )
    assert can_do is False


async def _setup_project_dag_template_and_run(
    user_email: str, role: str
) -> Tuple[DAGRun, DAGTemplate, Project, User]:
    (
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_and_dag_template(user_email, role)
    dag_run = await DAGRun.objects.acreate(
        dag_template=dag_template,
        run_start_time=datetime.datetime.now() - datetime.timedelta(days=1),
        run_end_time=datetime.datetime.now(),
        run_status="success",
        tags={},
        launched_by=user_creating_project,
        inputs={},
        outputs=[],
    )
    return dag_run, dag_template, project, user_creating_project


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role,allowed",
    [
        ("read", False),
        ("write", True),
    ],
)
async def test_user_can_write_to_dag_run_with_access(db, role, allowed):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    can_do, message = await user_can_write_to_dag_run(authenticated_request, dag_run_id=dag_run.id)
    assert can_do is allowed, message


@pytest.mark.asyncio
async def test_user_cannot_write_to_dag_run_with_no_access(db):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_write_to_dag_run(authenticated_request, dag_run_id=dag_run.id)
    assert can_do is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role",
    [
        "read",
        "write",
    ],
)
async def test_user_can_get_dag_runs_by_dag_run_id_with_access(db, role):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    can_do, message = await user_can_get_dag_runs(
        authenticated_request, dag_run_ids=str(dag_run.id)
    )
    assert can_do is True, message


@pytest.mark.asyncio
async def test_user_cannot_get_dag_run_with_no_access(db):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    can_do, message = await user_can_get_dag_runs(
        authenticated_request, dag_run_ids=str(dag_run.id)
    )
    assert can_do is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role,by,allowed",
    [
        ("read", "project_id", True),
        ("write", "project_id", True),
        ("read", "dag_template_id", True),
        ("write", "dag_template_id", True),
    ],
)
async def test_user_can_get_dag_runs_with_access(db, role, by, allowed):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", role)
    authenticated_request = await _get_authenticated_request("user_individual@no_team.com")
    kwargs = {}
    if by == "project":
        kwargs["project_id"] = project.id
    elif by == "dag_template":
        kwargs["dag_template_id"] = dag_template.id

    can_do, message = await user_can_get_latest_dag_runs(authenticated_request, **kwargs)
    assert can_do is allowed, message


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "by",
    [
        "project_id",
        "dag_template_id",
    ],
)
async def test_user_cannot_get_dag_runs_with_no_access(db, by):
    (
        dag_run,
        dag_template,
        project,
        user_creating_project,
    ) = await _setup_project_dag_template_and_run("user_individual@no_team.com", "write")
    authenticated_request = await _get_authenticated_request(
        "user_with_no_permissions@no_one_invited_me.com"
    )
    kwargs = {}
    if by == "project_id":
        kwargs["project_id"] = project.id
    elif by == "dag_template_id":
        kwargs["dag_template_id"] = dag_template.id

    can_do, message = await user_can_get_latest_dag_runs(authenticated_request, **kwargs)
    assert can_do is False, message
