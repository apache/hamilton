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

import typing

from common.django_utils import amap
from ninja.errors import HttpError
from trackingserver_auth.models import APIKey, Team
from trackingserver_base.permissions.base import allowed
from trackingserver_projects.models import Project, ProjectTeamMembership, ProjectUserMembership
from trackingserver_projects.schema import ProjectIn, ProjectUpdate, Visibility
from trackingserver_run_tracking.models import DAGRun
from trackingserver_template.models import DAGTemplate

"""The basic security design is as follows:
1. [Authentication] The user is authenticated, either by:
    a. A valid API key
    b. A valid JWT token (with Auth: bearer)
2. [Permission] We have a check on every API endpoint that asks if the user has permission
    to access the endpoint with any provided parameters. This is done by the decorator @permission,
    which takes a function that takes the request and any parameters and returns whether or not
    the user has access permission to any in there
3. [Visibility] Inside any "get" endpoints, we only access the items to which the user has visibility.


This is cumbersome, but multiple layers will help for now, and are easy to implement.

TODO -- add a test that every endpoint is decorated with @permission.
"""

# Curently any user can create a project
# This might change as we have more complex billing/auth scheme

# Filtering is done in the endpoint as
# it is a filtering operation rather than a permission operation
# E.G. all users can grab projects they own, so there's nothing
# worth filtering from the endpoint parameters
user_can_get_projects = allowed
user_can_get_api_keys = allowed

# All users can grab their own API keys/create their own
user_can_get_whoami = allowed
user_can_phone_home = allowed
user_can_create_api_key = allowed


async def user_can_delete_api_key(request: typing.Any, api_key_id: int) -> typing.Tuple[bool, str]:
    """Checks if a user can delete an API key.

    @param request:
    @return:
    """
    error = f"Could not delete API key: {api_key_id}"
    user, _ = request.auth
    try:
        api_key = await APIKey.objects.aget(id=api_key_id)
    except APIKey.DoesNotExist:
        return False, error
    if api_key.user_id != user.id:
        return False, error
    return True, ""


async def _visibility_valid_for_user(request, visibility: Visibility) -> bool:
    # TODO -- double-check that the user is contained within the visibility or a team thereof
    user, orgs = request.auth
    if "dagworks" in {org.name.lower() for org in orgs}:
        return True
    public_org = await Team.objects.aget(name="Public")
    visibility = await visibility.resolve_ids()
    for org in visibility.team_ids_visible + visibility.team_ids_writable:
        if org == public_org.id:
            return False
    return True


async def user_can_create_project(request, project: ProjectIn) -> typing.Tuple[bool, str]:
    """Any user can create a project. They just have to be logged in.
    The only exception is if they have "public" on their project, then it can't be created
    unless they're a DAGWorks member.

    @param request:
    @return:
    """
    visibility_valid = await _visibility_valid_for_user(request, project.visibility)
    if not visibility_valid:
        return False, "Cannot create/edit a project with public visibility"
    return True, ""


async def user_project_visibility(request, project: Project) -> typing.Optional[str]:
    user_memberships = await amap(
        lambda membership: membership.role,
        ProjectUserMembership.objects.filter(project=project.id, user=request.auth[0]).all(),
    )
    public_team = await Team.objects.aget(name="Public")
    team_memberships = await amap(
        lambda membership: membership.role,
        ProjectTeamMembership.objects.filter(
            project=project.id, team__in=request.auth[1] + [public_team]
        ).all(),
    )
    if "write" in team_memberships or "write" in user_memberships:
        return "write"
    if "read" in team_memberships or "read" in user_memberships:
        return "read"
    return None


async def user_can_get_project_by_id(request, project_id: int) -> typing.Tuple[bool, str]:
    """Checks if a user can get a project by ID, given a certain ID

    @param request:
    @param project_id:
    @return:
    """
    error_message = f"Could not find project with ID: {project_id}"
    try:
        project = await Project.objects.aget(id=project_id)
    except Project.DoesNotExist:
        return False, error_message
    visibility = await user_project_visibility(request, project)
    if visibility is None:
        return False, error_message
    return True, ""


async def user_can_write_to_project(request, project_id: int):
    error_message = f"Could not update project with ID: {project_id}"
    try:
        project_in_db = await Project.objects.aget(id=project_id)
    except Project.DoesNotExist:
        return False, error_message
    visibility = await user_project_visibility(request, project_in_db)
    if visibility != "write":
        return False, error_message
    return True, ""


async def user_can_update_project(
    request, project: ProjectUpdate, project_id: int
) -> typing.Tuple[bool, str]:
    """Checks if a user can get a project by ID, given a certain ID

    @param request: Request with auth information
    @param project_id: Project ID to update
    @return: Tuple of (can_update, error_message)
    """
    can_edit, message = await user_can_write_to_project(request, project_id)
    if not can_edit:
        return False, message
    if project.visibility is not None:
        visibility_valid = await _visibility_valid_for_user(request, project.visibility)
        if not visibility_valid:
            return False, "Invalid project visibility settings"
    return True, ""


async def user_can_get_dag_template(
    request: typing.Any, dag_template_ids: str
) -> typing.Tuple[bool, str]:
    """Tells whether or not the user can get a DAG template. This is only visible
    iff the project with which the corresponding project version is associated is visible.

    @param request:
    @param dag_template_id:
    @return:
    """
    dag_template_ids_parsed = [int(item) for item in dag_template_ids.split(",")]
    templates = [item async for item in DAGTemplate.objects.filter(id__in=dag_template_ids_parsed)]
    # TODO -- make this call more efficient.
    # We should have a bulk project version read that does one DB call?
    for template in templates:
        can_read_project_version, message = await user_can_get_project_by_id(
            request, template.project_id
        )
        if not can_read_project_version:
            return False, f"Could not find DAG template with ID: {dag_template_ids}"
    return True, ""


async def user_can_update_dag_template(request: typing.Any, dag_template_id: int):
    dag_template = await DAGTemplate.objects.aget(id=dag_template_id)
    can_write_project, message = await user_can_write_to_project(request, dag_template.project_id)
    if not can_write_project:
        return False, f"Could not write to DAG template with ID: {dag_template_id}"
    return True, ""


async def user_can_get_dag_templates(
    request: typing.Any, project_id: int
) -> typing.Tuple[bool, str]:
    if project_id is not None:
        can_read_project, message = await user_can_get_project_by_id(request, project_id)
        if not can_read_project:
            return False, f"Could not find project with ID: {project_id}"
    return True, ""


async def user_can_write_to_dag_template(request: typing.Any, dag_template_id: int):
    """Tells whether or not the user can update a DAG template. This is true
    iff the user can write to the associated template's project version's project.

    @param request: Django request
    @param dag_template_id: DAG Template ID in question
    @return: Tuple of (can_write, error_message)
    """

    templates = [item async for item in DAGTemplate.objects.filter(id=dag_template_id)]
    if len(templates) == 0:
        return False, f"Could not write to DAG template with ID: {dag_template_id}"
    (template,) = templates
    can_write_project, message = await user_can_write_to_project(request, template.project_id)
    if not can_write_project:
        return False, f"Could not write to DAG template with ID: {dag_template_id}"
    return True, ""


async def user_can_get_dag_runs(request: typing.Any, dag_run_ids: str):
    """Tells whether or not the user can update a DAG run. This is true
    iff the user can write to the associated template's project version's project.

    @param request: Django request
    @param dag_run_id: DAG run ID in question
    @return: Tuple of (can_write, error_message)
    """
    dag_run_ids_parsed = [int(item) for item in dag_run_ids.split(",")]
    dag_runs = [
        item
        async for item in DAGRun.objects.filter(id__in=dag_run_ids_parsed).prefetch_related(
            "dag_template"
        )
    ]
    if len(dag_runs) != len(dag_run_ids_parsed):
        return False, f"Could not read DAG run with ID: {dag_runs}"
    # we could make this more efficient but its fine for now
    project_ids = {dag_run.dag_template.project_id for dag_run in dag_runs}
    if len(project_ids) != 1:
        raise HttpError(422, "DAG runs must be from the same project")
    (project_id,) = list(project_ids)
    can_write_project, message = await user_can_get_project_by_id(request, project_id)
    if not can_write_project:
        return False, f"Could not write to DAG run with ID: {dag_run_ids_parsed}"
    return True, ""


async def user_can_write_to_dag_run(request: typing.Any, dag_run_id: int):
    """Tells whether or not the user can update a DAG run. This is true
    iff the user can write to the associated template's project version's project.

    @param request: Django request
    @param dag_run_id: DAG run ID in question
    @return: Tuple of (can_write, error_message)
    """
    dag_runs = [
        item async for item in DAGRun.objects.filter(id=dag_run_id).prefetch_related("dag_template")
    ]
    if len(dag_runs) == 0:
        return False, f"Could not write to DAG run with ID: {dag_run_id}"
    (dag_run,) = dag_runs
    can_write_project, message = await user_can_write_to_project(
        request, dag_run.dag_template.project_id
    )
    if not can_write_project:
        return False, f"Could not write to DAG run with ID: {dag_run_id}"
    return True, ""


async def user_can_get_latest_dag_runs(
    request: typing.Any,
    project_id: int = None,
    dag_template_id: int = None,
):
    """Tells whether or not the user can get a list of latest DAG runs. This is true
    if the user can get the associated project, project version, or DAG template
    (the one that is specified by the request).

    @param request: Django request
    @param project_id: Project ID in question
    @param project_version_id: Project version ID in question
    @param dag_template_id: DAG template ID in question
    @return: Tuple of (can_get, error_message)
    """
    if project_id is not None:
        can_read_project, message = await user_can_get_project_by_id(request, project_id)
        if not can_read_project:
            return False, f"Could not find project with ID: {project_id}"
    if dag_template_id is not None:
        can_read_dag_template, message = await user_can_get_dag_template(
            request, str(dag_template_id)
        )
        if not can_read_dag_template:
            return False, f"Could not find DAG template with ID: {dag_template_id}"
    return True, ""
