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

from ninja import ModelSchema, Schema
from pydantic import Field
from trackingserver_auth.models import APIKey, Team, User, UserTeamMembership


##########################################
# These correspond (ish) to DB models    #
##########################################
class UserOut(ModelSchema):
    class Config:
        model = User
        model_fields = ["id", "email", "first_name", "last_name"]


class TeamOut(ModelSchema):
    class Config:
        model = Team
        model_fields = ["id", "name", "auth_provider_type", "auth_provider_organization_id"]


class ApiKeyOut(ModelSchema):
    class Config:
        model = APIKey
        model_fields = ["id", "key_name", "key_start", "is_active", "created_at", "updated_at"]


##########################################
#           Purely for the API           #
##########################################


class ApiKeyIn(Schema):
    name: str = Field(description="The name of the API key")


class PhoneHomeResult(Schema):
    success: bool = Field(description="The result of the phone home")
    message: str = Field(description="The message associated with the result")


class WhoAmIResult(Schema):
    user: UserOut
    teams: typing.List[TeamOut]

    @staticmethod
    async def from_user(user: User) -> "WhoAmIResult":
        memberships = UserTeamMembership.objects.filter(user__id=user.id).select_related("team")
        teams = [TeamOut.from_orm(membership.team) async for membership in memberships]

        return WhoAmIResult(user=UserOut.from_orm(user), teams=teams)
        # return WhoAmIResult(
        #     user=UserOut.from_orm(user),
        #     teams=[TeamOut.from_orm(membership.team) async
        #            for membership in UserTeamMembership.objects.filter(user__id=user.id)])
