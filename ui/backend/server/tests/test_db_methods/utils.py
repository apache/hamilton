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
from typing import List, Optional

from trackingserver_auth.models import Team, User, UserTeamMembership


async def setup_sample_user_random():
    """Create a sample user for testing."""
    auth_provider_user_id = str(uuid.uuid4())
    user_email_prefix = uuid.uuid4()
    email = f"{user_email_prefix}@test_ensure_user_exists_user_already_exists.io"
    user = User(
        email=email,
        first_name="test",
        last_name="test",
        auth_provider_type="test",
        auth_provider_user_id=auth_provider_user_id,
    )
    await user.asave()
    return user


async def setup_sample_team_random():
    """Create a sample team for testing."""
    auth_provider_org_id = str(uuid.uuid4())
    team_name = str(uuid.uuid4())
    team = Team(
        auth_provider_organization_id=auth_provider_org_id,
        auth_provider_type="propel_auth",
        name=team_name,
    )
    await team.asave()
    return team


async def setup_random_user_with_n_teams(n: int):
    user = await setup_sample_user_random()
    teams = []
    for _ in range(n):
        team = await setup_sample_team_random()
        teams.append(team)
    for team in teams:
        await UserTeamMembership.objects.acreate(user=user, team=team)
    return user, teams


async def assert_user_state(email: str, exists: bool) -> Optional[User]:
    try:
        out = await User.objects.aget(email=email)
        assert exists, "User should exist"
        return out
    except User.DoesNotExist:
        assert not exists, "User should not exist"


async def assert_team_state(team_id: str, exists: bool) -> Optional[Team]:
    try:
        out = await Team.objects.aget(auth_provider_organization_id=team_id)
        assert exists, "Team should exist"
        return out
    except Team.DoesNotExist:
        assert not exists, "Team should not exist"


async def assert_user_only_part_of_teams(
    user: User,
    teams: List[Team],
):
    memberships = [
        item
        async for item in UserTeamMembership.objects.filter(user=user)
        .prefetch_related("team")
        .all()
    ]
    assert len(memberships) == len(teams)
    for membership in memberships:
        assert membership.team in teams
