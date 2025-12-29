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

import pytest
from django.forms import model_to_dict
from trackingserver_auth.models import Team, User
from trackingserver_base.auth.sync import (
    ensure_team_exists,
    ensure_user_exists,
    ensure_user_only_part_of_orgs,
)

from tests.test_db_methods.utils import (
    assert_team_state,
    assert_user_only_part_of_teams,
    assert_user_state,
    setup_random_user_with_n_teams,
    setup_sample_team_random,
)


@pytest.mark.asyncio
async def test_ensure_user_exists_does_not_exist_yet(db):
    # random_email
    auth_provider_user_id = str(uuid.uuid4())
    user_email_prefix = uuid.uuid4()
    email = f"{user_email_prefix}@test_ensure_user_exists_does_not_exist_yet.io"
    await assert_user_state(email=email, exists=False)
    user = await ensure_user_exists(auth_provider_user_id=auth_provider_user_id, user_email=email)
    user_from_db = await assert_user_state(email=email, exists=True)
    assert model_to_dict(user) == model_to_dict(user_from_db)


@pytest.mark.asyncio
async def test_ensure_user_exists_already_exists(db):
    auth_provider_user_id = str(uuid.uuid4())
    user_email_prefix = uuid.uuid4()
    email = f"{user_email_prefix}@test_ensure_user_exists_user_already_exists.io"
    await assert_user_state(email=email, exists=False)
    user = User(
        email=email,
        first_name="test",
        last_name="test",
        auth_provider_type="test",
        auth_provider_user_id=auth_provider_user_id,
    )
    await user.asave()
    await assert_user_state(email=email, exists=True)
    # This will break if it doesn't exist
    user_ensured = await ensure_user_exists(
        auth_provider_user_id=user.auth_provider_user_id, user_email=user.email
    )
    user_from_db = await assert_user_state(email=email, exists=True)
    assert user_ensured.email == user_from_db.email


@pytest.mark.asyncio
async def test_ensure_team_exists_does_not_exist_yet(db):
    auth_provider_org_id = str(uuid.uuid4())
    team_name = str(uuid.uuid4())
    await assert_team_state(team_id=auth_provider_org_id, exists=False)
    team = await ensure_team_exists(org_id=auth_provider_org_id, team_name=team_name)
    team_from_db = await assert_team_state(team_id=auth_provider_org_id, exists=True)
    assert model_to_dict(team) == model_to_dict(team_from_db)


@pytest.mark.asyncio
async def test_ensure_team_exists_team_already_exists(db):
    auth_provider_org_id = str(uuid.uuid4())
    team_name = str(uuid.uuid4())
    await assert_team_state(team_id=auth_provider_org_id, exists=False)
    team = Team(
        name=team_name,
        auth_provider_type="test",
        auth_provider_organization_id=auth_provider_org_id,
    )
    await team.asave()
    await assert_team_state(team_id=auth_provider_org_id, exists=True)
    # This will break if it doesn't exist
    team_ensured = await ensure_team_exists(
        org_id=team.auth_provider_organization_id, team_name=team.name
    )
    team_from_db = await assert_team_state(team_id=auth_provider_org_id, exists=True)
    assert team_ensured.name == team_from_db.name


@pytest.mark.asyncio
async def test_ensure_user_only_part_of_orgs_noop(db):
    user, teams = await setup_random_user_with_n_teams(3)
    await ensure_user_only_part_of_orgs(user, teams)
    await assert_user_state(user.email, exists=True)
    await assert_user_only_part_of_teams(user, teams)


@pytest.mark.asyncio
async def test_ensure_user_only_part_of_orgs_make_changes(db):
    user, teams = await setup_random_user_with_n_teams(3)
    # should be part of 4 teams
    teams_should_be_part_of = teams[:2]
    additional_teams = [
        await setup_sample_team_random(),
        await setup_sample_team_random(),
    ]
    all_teams_user_should_be_part_of = teams_should_be_part_of + additional_teams
    await ensure_user_only_part_of_orgs(user, all_teams_user_should_be_part_of)
    await assert_user_state(user.email, exists=True)
    await assert_user_only_part_of_teams(user, all_teams_user_should_be_part_of)
