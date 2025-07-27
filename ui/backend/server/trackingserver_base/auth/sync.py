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
import os
from typing import List

from trackingserver_auth.models import Team, User, UserTeamMembership
from trackingserver_base import notifications

logger = logging.getLogger(__name__)


async def ensure_user_only_part_of_orgs(user: User, orgs: List[Team]):
    """Ensures that the user is part of the organization.
    If not, adds them to the organization.
    @param user: Relevant user
    @param org: Relevant organization
    """
    # orgs_user_is_currently_part_of = {org.id for org in user.teams.all()}
    user_is_currently_part_of = {
        item.team
        async for item in UserTeamMembership.objects.filter(user=user)
        .all()
        .prefetch_related("team")
    }
    user_should_be_part_of = {org for org in orgs}
    if user_is_currently_part_of == user_should_be_part_of:
        return  # nothing to do
    user_should_be_removed_from = user_is_currently_part_of - user_should_be_part_of
    user_should_be_added_to = user_should_be_part_of - user_is_currently_part_of

    logger.info(
        f"User {user.email} should not be part of orgs {user_should_be_removed_from}, removing from db"
    )
    memberships_to_remove = await UserTeamMembership.objects.filter(
        user=user, team__in=user_should_be_removed_from
    ).adelete()
    logger.info(f"Removed {user.email} from {len(memberships_to_remove)} memberships")
    logger.info(f"User {user.email} should be part of orgs {user_should_be_part_of}, adding to db")
    memberships_to_add = [
        UserTeamMembership(user=user, team=team) for team in user_should_be_added_to
    ]
    await UserTeamMembership.objects.abulk_create(memberships_to_add)
    logger.info(f"Added {user.email} to {len(memberships_to_add)} memberships")


async def ensure_team_exists(org_id: str, team_name: str) -> Team:
    """Ensures that the organization exists in the database.
    If not, creates it.

    @param org_id: ID of the organization in the auth provider
    @param org_name: Name of the organization
    @return: The organization, if it exists, otherwise the organization that was created
    """
    try:
        team_model = await Team.objects.aget(auth_provider_organization_id=org_id)
    except Team.DoesNotExist:
        logger.info(f"Creating new organization {team_name} with auth id {org_id}")
        team_model = Team(
            auth_provider_organization_id=org_id,
            auth_provider_type="propel_auth",
            name=team_name,
        )
        await team_model.asave()
    return team_model


async def ensure_user_exists(auth_provider_user_id: str, user_email: str) -> User:
    """Ensures that a user exists in the database.
    If not, creates it.

    @param propel_auth_user_id: ID of the user in the auth provider
    @param user_email: Email of the user
    @return: The user, if it exists, otherwise the user that was created
    """
    try:
        logger.debug(
            f"Looking up user with propel auth id {auth_provider_user_id} and email {user_email}"
        )
        user_model = await User.objects.aget(auth_provider_user_id=auth_provider_user_id)
    except User.DoesNotExist:
        logger.warning(
            f"Creating new user {user_email} with auth provider ID " f"id {auth_provider_user_id}"
        )
        user_model = User(
            auth_provider_user_id=auth_provider_user_id,
            email=user_email,
        )
        await user_model.asave()
        env = os.environ.get("HAMILTON_ENV", "dev")
        if env == "prod":
            await notifications.user_signup_notification(user_model)
    return user_model
