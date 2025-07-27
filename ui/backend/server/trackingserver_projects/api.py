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

import logging
import typing

from django.db.models import Q
from ninja import Router
from ninja.errors import HttpError
from trackingserver_auth.models import Team, User
from trackingserver_base.permissions.base import permission
from trackingserver_base.permissions.permissions import (
    user_can_create_project,
    user_can_get_project_by_id,
    user_can_get_projects,
    user_can_update_project,
    user_project_visibility,
)
from trackingserver_projects.models import (
    Project,
    ProjectAttribute,
    ProjectMembership,
    ProjectTeamMembership,
    ProjectUserMembership,
)
from trackingserver_projects.schema import (  # ProjectVersionIn,; ProjectVersionOut,; ProjectVersionOutWithCode,
    ProjectAttributeIn,
    ProjectAttributeOut,
    ProjectIn,
    ProjectOut,
    ProjectOutWithAttributes,
    ProjectUpdate,
    Visibility,
)

logger = logging.getLogger(__name__)
router = Router(tags=["projects"])


async def _add_attributes_to_project(
    project: Project, attributes: typing.List[ProjectAttributeIn]
) -> typing.List[ProjectAttribute]:
    attributes_to_add = []
    for attribute in attributes:
        attribute_to_add = ProjectAttributeIn.to_model(attribute, project_id=project.id)
        attributes_to_add.append(attribute_to_add)
    logger.info(f"Saving {len(attributes_to_add)} attributes")
    return await ProjectAttribute.objects.abulk_create(attributes_to_add)


# TODOO -- use transactions with sync_to_async
# Or use the first solutino here: https://stackoverflow.com/questions/74575922/how-to-use-transaction-with-async-functions-in-django
async def _update_project_membership(
    project: Project, visibility: Visibility
) -> typing.List[ProjectMembership]:
    """This is lazy -- it just deletes then rewrites it. This is rarely done so I'm not worried.

    @param project: Project to update
    @param visibility:  Visibility object to update
    @return: A list of memberships that now exist
    """
    logger.info(f"Deleting current memberships for project {project.name} with id {project.id}")
    await ProjectTeamMembership.objects.filter(project_id=project.id).adelete()
    await ProjectUserMembership.objects.filter(project_id=project.id).adelete()
    team_memberships, user_memberships = visibility.to_memberships(project)
    logger.info(
        f"Saving {len(team_memberships)} team memberships for project {project.name} with id {project.id}"
    )
    logger.info(
        f"Saving {len(user_memberships)} user memberships for project {project.name} with id {project.id}"
    )
    out = await ProjectTeamMembership.objects.abulk_create(team_memberships)
    out += await ProjectUserMembership.objects.abulk_create(user_memberships)
    return out


@router.post("/v1/projects", response=ProjectOut, tags=["projects"])
@permission(user_can_create_project)
async def create_project(request, project: ProjectIn) -> ProjectOut:
    """Creates a project. User specifies visibility -- it will always be user-visible.

    @param request: Request from django ninja
    @param project: Project to create
    @param visibility: Visibility object of the project -- todo -- replace this with a cleaner mechanism
    @param attributes: Attributes to add to the project
    @param project:
    @return:
    """
    user, orgs = request.auth
    visibility = await project.visibility.resolve_ids()
    project_created = await Project.objects.acreate(
        name=project.name,
        description=project.description,
        creator=user,
        tags=project.tags,
    )
    attributes = project.attributes if project.attributes is not None else []
    memberships_added = await _update_project_membership(project_created, visibility)
    logger.info(
        f"Added {len(memberships_added)} memberships to project {project_created.name} for {user.email} with id {project_created.id}"
    )
    attributes_added = await _add_attributes_to_project(project_created, attributes)
    logger.info(
        f"Added {len(attributes_added)} attributes to project {project_created.name} for {user.email} with id {project_created.id}"
    )
    # TODO -- optimize this if needed, shouldn't be too slow
    role = await user_project_visibility(request, project_created)
    return await ProjectOut.from_model(project_created, role=role)


@router.get(
    "/v1/projects/{project_id}",
    response=typing.Optional[ProjectOutWithAttributes],
    tags=["projects"],
)
@permission(user_can_get_project_by_id)
async def get_project_by_id(
    request, project_id: int, attribute_types: typing.Optional[str] = None
) -> ProjectOutWithAttributes:
    """Gets a project by ID

    @param request: Django request
    @param project_id:
    @return: Null if project does not exist, else the project
    """
    # user, orgs = request.auth
    attribute_types = (attribute_types if attribute_types is not None else "").split(",")
    try:
        project = await Project.objects.aget(id=project_id)
    except Project.DoesNotExist:
        raise HttpError(404, f"Could not find project with ID: {project_id}") from None
    role = await user_project_visibility(request, project=project)
    project_out = await ProjectOut.from_model(project, role)
    attributes = [
        ProjectAttributeOut.from_orm(item)
        async for item in ProjectAttribute.objects.filter(
            project_id=project_id, type__in=attribute_types
        ).all()
    ]
    return ProjectOutWithAttributes(**project_out.dict(), attributes=attributes)


@router.put("/v1/projects/{project_id}", response=ProjectOut, tags=["projects"])
@permission(user_can_update_project)
async def update_project(
    request,
    project_id: int,
    project: ProjectUpdate,
    attributes: typing.List[ProjectAttributeIn] = None,
) -> ProjectOut:
    """Updates a project. Note that attributes are append only.

    @param request:
    @param project_id:
    @param project:
    @param visibility:
    @param attributes:
    @return:
    """
    user, orgs = request.auth
    visibility = await project.visibility.resolve_ids() if project.visibility is not None else None
    logger.info(f"Updating project {project.name} for {user.email}")
    project_to_update: Project = await Project.objects.aget(id=project_id)

    for field in project.dict(exclude_unset=True):
        # Visibility is special -- that turns into a membership table
        if field is not None and field != "visibility":
            setattr(project_to_update, field, getattr(project, field))

    await project_to_update.asave()
    if visibility is not None:
        memberships_added = await _update_project_membership(project_to_update, visibility)
        logger.info(
            f"Added {len(memberships_added)} memberships to project {project_to_update.name} for {user.email} with id {project_to_update.id}"
        )
    if attributes is not None:
        attributes_added = await _add_attributes_to_project(project_to_update, attributes)
        logger.info(
            f"Added {len(attributes_added)} attributes to project {project_to_update.name} for {user.email} with id {project_to_update.id}"
        )
    logger.info(f"Updated project {project.name} for {user.email}")
    role = await user_project_visibility(request, project=project_to_update)
    return await ProjectOut.from_model(project_to_update, role=role)


async def _get_visible_projects(
    user: User, organizations: typing.List[Team], limit: int, offset: int = None
) -> typing.List[typing.Tuple[Project, str]]:
    """Gets all projects that the user has access to

    @param user: The user
    @param organization: The organization
    @return: A list of projects
    """
    # prefetch_related allows us to grab data that we might want
    # to use later without having to make additional queries
    # we're very likely going to want to fix this query, given that we use the `.distinct()`
    # call at the end. For now its fine though.
    org_ids = [org.id for org in organizations]
    # Async for is required as django does not currently support async property access individually
    all_project_memberships = [
        item
        async for item in Project.objects.filter(
            Q(projectusermembership__user_id=user.id)
            | Q(projectteammembership__team_id__in=org_ids)
        )
        .distinct()
        .order_by("-created_at")[offset : offset + limit]
        .prefetch_related("projectusermembership_set", "projectteammembership_set")
    ]
    # This shouldn't be too slow -- we're prefetching related, and the project cardinality should be reasonable
    out = [
        (
            project,
            (
                "write"
                if any(
                    [
                        project_membership.role == "write"
                        for project_membership in list(project.projectusermembership_set.all())
                        + list(project.projectteammembership_set.all())
                    ]
                )
                else "read"
            ),
        )
        for project in all_project_memberships
    ]
    return out
    # return visible_projects


@router.get("/v1/projects", response=typing.List[ProjectOutWithAttributes], tags=["projects"])
@permission(user_can_get_projects)
async def get_projects(
    request, attribute_types: typing.Optional[str] = None, limit: int = 100, offset: int = 0
) -> typing.List[ProjectOutWithAttributes]:
    """Gets a list of projects visible by a user, auto-paginating.
    TODO -- fix to use actual pagination on the db side

    @param offset:
    @param limit:
    @param attribute_types:
    @param request:
    @return: A list of projects
    """
    user, orgs = request.auth
    orgs: typing.List[Team]
    user: User
    attribute_types = attribute_types.split(",") if attribute_types is not None else []
    logger.info(f"Getting projects for {user.email} with orgs: {[org.name for org in orgs]}")
    projects = await _get_visible_projects(user, orgs, limit, offset)
    logger.info(
        f"Got {len(projects)} projects for {user.email} with orgs: {[org.name for org in orgs]}"
    )
    # TODO -- test if this is horribly slow
    projects = await ProjectOut.from_models([project for project, role in projects], user, orgs)
    logger.info(
        f"Parsed {len(projects)} projects for {user.email} with orgs: {[org.name for org in orgs]}"
    )
    # TODO -- merge this with the above and get a much better/cleaner query
    attributes = [
        item
        async for item in ProjectAttribute.objects.filter(
            project_id__in=[project.id for project in projects], type__in=attribute_types
        ).all()
    ]
    project_id_to_attributes = {}
    for attribute in attributes:
        if attribute.project_id not in project_id_to_attributes:
            project_id_to_attributes[attribute.project_id] = []
        project_id_to_attributes[attribute.project_id].append(
            ProjectAttributeOut.from_orm(attribute)
        )
    return [
        ProjectOutWithAttributes(
            **project.dict(), attributes=project_id_to_attributes.get(project.id, [])
        )
        for project in projects
    ]
