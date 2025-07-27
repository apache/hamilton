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

import datetime
import logging
import typing

from ninja import ModelSchema, Schema
from pydantic import Field
from trackingserver_auth.models import Team, User
from trackingserver_auth.schema import TeamOut, UserOut
from trackingserver_projects.models import (
    Project,
    ProjectAttribute,
    ProjectMembership,
    ProjectTeamMembership,
    ProjectUserMembership,
)

logger = logging.getLogger(__name__)


class VisibilityFull(Schema):
    pass


class ProjectAttributeIn(ModelSchema):
    class Config:
        model = ProjectAttribute
        model_fields = ["name", "type", "schema_version", "value"]


class ProjectAttributeOut(ModelSchema):
    class Config:
        model = ProjectAttribute
        model_fields = ["name", "type", "schema_version", "value", "id", "project"]


class ProjectTeamMembershipOut(ModelSchema):
    class Config:
        model = ProjectTeamMembership
        model_fields = "__all__"


class ProjectUserMembershipOut(ModelSchema):
    class Config:
        model = ProjectUserMembership
        model_fields = "__all__"


# This is currently the schema we take from the UI
# Its suboptimal, as we should be doing the following:
#   1. Creating invites if someone does not exist
#   2. Looking up the IDs of the users/teams on the FE so we can just pass them in as...
#   3. Pass them in as memberships, not as the VisibilityIn object
# For now this is easy enough to not have to worry about this and the API is not public -- TODO -- implement!
class Visibility(Schema):
    # Note that the str for user_ids_visible can be an email, in which case we'll do a lookup
    # It will always save an ID
    user_ids_visible: typing.List[typing.Union[int, str]]
    team_ids_visible: typing.List[int]
    team_ids_writable: typing.List[int]
    user_ids_writable: typing.List[typing.Union[int, str]]

    async def resolve_ids(self) -> "Visibility":
        """Resolves the user_ids_visible and user_ids_writable to IDs
        @param self:
        @param user:
        @return:
        """
        all_emails = [
            item for item in self.user_ids_visible + self.user_ids_writable if isinstance(item, str)
        ]
        email_map = {
            user.email: user.id async for user in User.objects.filter(email__in=all_emails)
        }
        non_existing_emails = [email for email in all_emails if email not in email_map]
        if len(non_existing_emails) > 0:
            logger.warning(
                f"Could not find users with emails {non_existing_emails}, proceeding with edit anyway..."
            )

        user_ids_visible_to_save = [
            email_map[user_id] if user_id in email_map else user_id
            for user_id in self.user_ids_visible
            if user_id not in non_existing_emails
        ]
        user_ids_writable_to_save = [
            email_map[user_id] if user_id in email_map else user_id
            for user_id in self.user_ids_writable
            if user_id not in non_existing_emails
        ]
        return Visibility(
            user_ids_visible=user_ids_visible_to_save,
            team_ids_visible=self.team_ids_visible,
            user_ids_writable=user_ids_writable_to_save,
            team_ids_writable=self.team_ids_writable,
        )

    def to_memberships(
        self, project: Project
    ) -> typing.Tuple[typing.List[ProjectTeamMembership], typing.List[ProjectUserMembership]]:
        """Converts the visibility object to a list of memberships

        @param project:
        @param self:
        @return:
        """
        team_memberships = []
        user_memberships = []
        for team_writable in self.team_ids_writable:
            team_memberships.append(
                ProjectTeamMembership(project=project, team_id=team_writable, role="write")
            )
        for user_writable in self.user_ids_writable:
            user_memberships.append(
                ProjectUserMembership(project=project, user_id=user_writable, role="write")
            )
        for team_visible in self.team_ids_visible:
            team_memberships.append(
                ProjectTeamMembership(project=project, team_id=team_visible, role="read")
            )
        for user_visible in self.user_ids_visible:
            user_memberships.append(
                ProjectUserMembership(project=project, user_id=user_visible, role="read")
            )
        return team_memberships, user_memberships

    @staticmethod
    def from_memberships(memberships: typing.List[ProjectMembership]) -> "Visibility":
        """Gets the visibility object from a list of memberships

        @param memberships:
        @return:
        """
        visibility = Visibility(
            user_ids_visible=[], team_ids_visible=[], team_ids_writable=[], user_ids_writable=[]
        )
        for membership in memberships:
            # TODO -- implement
            if isinstance(membership, ProjectTeamMembership):
                if membership.role == "write":
                    visibility.team_ids_writable.append(membership.team_id)
                elif membership.role == "read":
                    visibility.team_ids_visible.append(membership.team_id)
            elif isinstance(membership, ProjectUserMembership):
                if membership.role == "write":
                    visibility.user_ids_writable.append(membership.user_id)
                elif membership.role == "read":
                    visibility.user_ids_visible.append(membership.user_id)

        return visibility


class VisibilityOut(Schema):
    users_visible: typing.List[UserOut]
    users_writable: typing.List[UserOut]
    teams_visible: typing.List[TeamOut]
    teams_writable: typing.List[TeamOut]

    @staticmethod
    async def from_visibility(visibility: Visibility):
        """Creates a visibility out from a visibility

        @param visibility:
        @return:
        """
        user_ids = visibility.user_ids_visible + visibility.user_ids_writable
        team_ids = visibility.team_ids_visible + visibility.team_ids_writable
        users = [UserOut.from_orm(user) async for user in User.objects.filter(id__in=user_ids)]
        teams = [TeamOut.from_orm(team) async for team in Team.objects.filter(id__in=team_ids)]
        return VisibilityOut(
            users_visible=[user for user in users if user.id in visibility.user_ids_visible],
            users_writable=[user for user in users if user.id in visibility.user_ids_writable],
            teams_visible=[team for team in teams if team.id in visibility.team_ids_visible],
            teams_writable=[team for team in teams if team.id in visibility.team_ids_writable],
        )


class ProjectUpdate(Schema):
    name: typing.Optional[str] = Field(description="The name of the project", default=None)
    description: typing.Optional[str] = Field(
        description="Description of the project", default=None
    )
    tags: typing.Optional[typing.Dict[str, str]] = Field(
        description="Tags for the project", default=None
    )
    visibility: typing.Optional[Visibility] = Field(
        description="Visibility of the project", default=None
    )


class ProjectBase(Schema):
    name: str = Field(description="The name of the project")
    description: str = Field(description="Description of the project")
    tags: typing.Dict[str, str] = Field(description="Tags for the project")


class ProjectIn(ProjectBase):
    visibility: Visibility = Field(description="Visibility of the project")
    attributes: typing.List[ProjectAttributeIn] = Field(
        description="Attributes for the project", default=[]
    )


class ProjectOut(ProjectBase):
    id: int
    role: str = Field(description="Role of the user in the project", default=None)
    visibility: VisibilityOut = Field(description="Resolved visibility of the project")
    created_at: datetime.datetime = Field(description="When the project was created")
    updated_at: datetime.datetime = Field(description="When the project was last updated")

    class Config:
        model = Project
        model_fields = "__all__"

    @staticmethod
    async def from_model(project: Project, role: str) -> "ProjectOut":
        """Creates a project out from a model

        @param project:
        @return:
        """
        # TODO -- ensure that this isn't too slow...
        visibility = Visibility.from_memberships(
            [
                membership
                async for membership in ProjectTeamMembership.objects.filter(project=project)
            ]
            + [
                membership
                async for membership in ProjectUserMembership.objects.filter(project=project)
            ]
        )
        return ProjectOut(
            name=project.name,
            description=project.description,
            tags=project.tags,
            visibility=await VisibilityOut.from_visibility(visibility),
            id=project.id,
            role=role,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    @staticmethod
    async def from_models(
        projects: typing.List[Project], user: User, teams: typing.List[Team]
    ) -> typing.List["ProjectOut"]:
        """
        @return:
        """
        # We could easily prefetch related upstream but this is fine for now...
        all_team_memberships = [
            item
            async for item in ProjectTeamMembership.objects.filter(project__in=projects)
            .all()
            .prefetch_related("team")
        ]
        all_user_memberships = [
            item
            async for item in ProjectUserMembership.objects.filter(project__in=projects)
            .all()
            .prefetch_related("user")
        ]

        out = []
        team_ids = [team.id for team in teams]
        for project in projects:
            relevant_team_memberships = [
                item for item in all_team_memberships if item.project_id == project.id
            ]
            relevant_user_memberships = [
                item for item in all_user_memberships if item.project_id == project.id
            ]
            team_can_write = (
                len(
                    [
                        item
                        for item in relevant_team_memberships
                        if item.team_id in team_ids and item.role == "write"
                    ]
                )
                > 0
            )
            user_can_write = (
                len(
                    [
                        item
                        for item in relevant_user_memberships
                        if item.user_id == user.id and item.role == "write"
                    ]
                )
                > 0
            )
            role = "write" if team_can_write or user_can_write else "read"
            out.append(
                ProjectOut(
                    id=project.id,
                    name=project.name,
                    description=project.description,
                    tags=project.tags,
                    visibility=VisibilityOut(
                        users_visible=[
                            UserOut.from_orm(membership.user)
                            for membership in relevant_user_memberships
                            if membership.role == "read"
                        ],
                        users_writable=[
                            UserOut.from_orm(membership.user)
                            for membership in relevant_user_memberships
                            if membership.role == "write"
                        ],
                        teams_visible=[
                            TeamOut.from_orm(membership.team)
                            for membership in relevant_team_memberships
                            if membership.role == "read"
                        ],
                        teams_writable=[
                            TeamOut.from_orm(membership.team)
                            for membership in relevant_team_memberships
                            if membership.role == "write"
                        ],
                    ),
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                    role=role,
                )
            )
        return out


class ProjectOutWithAttributes(ProjectOut):
    attributes: typing.List[ProjectAttributeOut]
