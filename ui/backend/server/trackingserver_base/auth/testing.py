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
from typing import List, Optional, Tuple

from django.http import HttpRequest
from ninja.security.http import HttpAuthBase
from trackingserver_auth.models import Team, User, UserTeamMembership

logger = logging.getLogger(__name__)

TEST_USERS = {
    "user_individual@no_team.com": [],
    "user_1_team_1@team1.com": ["Team 1"],
    "user_1_team_2@team2.com": ["Team 2"],
    "user_with_no_permissions@no_one_invited_me.com": [],  # Dummy user that we don't create anything for
    "user_on_both_team_1_and_team_2@multiteam.com": [
        "Team 1",
        "Team 2",
    ],  # User that has access to team 1 and team 2
}


class TestAPIAuthenticator(HttpAuthBase):
    async def __call__(self, request: HttpRequest) -> Optional[Tuple[User, List[Team]]]:
        """This is a test authenticator that can be used for local development.

        TODO -- utilize ensure_* here when we've abstracted away auth a little more

        It will:
        0. Decide the user based on the "test_username" field in the request
        2. Error out if the user is not found in the test user list
        3. Create the user if it does not exist
        4. Create the team if it does not exist
        5. Ensure the user is part of the team

        @param request:
        @return:
        """
        username = request.headers.get("test_username")
        return await self.ensure(username)

    @staticmethod
    async def ensure(username: str):
        if not username:
            logger.warning("Received no test username to authenticate")
            return None
        if username not in TEST_USERS:
            logger.warning(f"Received invalid test username {username}")
            return None
        teams = []
        for team in TEST_USERS[username]:
            try:
                team_model = await Team.objects.aget(name=team)
            except Team.DoesNotExist:
                team_model = Team(
                    name=team, auth_provider_organization_id="", auth_provider_type=""
                )
                await team_model.asave()
            teams.append(team_model)
        try:
            user = await User.objects.aget(email=username)
        except User.DoesNotExist:
            logger.warning(f"Creating new user {username} with propel auth id {username}")
            user = User(
                first_name=username.split("@")[0],
                last_name="test",
                email=username,
            )
            await user.asave()
        memberships = UserTeamMembership.objects.filter(user__id=user.id)
        teams_user_is_currently_part_of = {membership.team_id async for membership in memberships}
        teams_user_should_be_part_of = {team.id for team in teams}
        if teams_user_is_currently_part_of != teams_user_should_be_part_of:
            logger.info(f"Updating user {user.email} to be part of teams {teams}")
            for team in teams_user_should_be_part_of:
                if team not in teams_user_is_currently_part_of:
                    await UserTeamMembership(
                        user=user, team=await Team.objects.aget(id=team)
                    ).asave()
            for team in teams_user_is_currently_part_of:
                if team not in teams_user_should_be_part_of:
                    await UserTeamMembership.objects.filter(
                        user__id=user.id, team__id=team
                    ).adelete()
        logger.info(f"Authenticated user {username} with teams {teams}")
        return user, teams
