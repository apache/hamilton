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

from ninja import Router
from trackingserver_auth.models import APIKey
from trackingserver_auth.schema import ApiKeyIn, ApiKeyOut, PhoneHomeResult, WhoAmIResult
from trackingserver_base.auth.api_keys import create_api_key_for_user
from trackingserver_base.permissions.base import permission
from trackingserver_base.permissions.permissions import (
    user_can_create_api_key,
    user_can_delete_api_key,
    user_can_get_api_keys,
    user_can_get_whoami,
    user_can_phone_home,
)

logger = logging.getLogger(__name__)
router = Router(tags=["auth"])


@router.get(
    "/v1/phone_home",
    response=PhoneHomeResult,
    tags=["auth"],
)
@permission(user_can_phone_home)
async def phone_home(request) -> PhoneHomeResult:
    """Quick authentication validator. Tells you if you username/auth setup are legit.

    @param request:
    @param username:
    @return:
    """
    user, orgs = request.auth
    logger.info(
        f"Phone home from {user.email} ({user.id}) belonging to orgs: {[org.name for org in orgs]}."
    )
    return PhoneHomeResult(success=True, message="You are authenticated!")


# TODO -- remove /v0/whoami, this is just for API testing prior to refactor/release
@router.get("/v1/whoami", response=WhoAmIResult, tags=["auth"])
@permission(user_can_get_whoami)
async def whoami(request) -> WhoAmIResult:
    """Gives information about who you are, for the UI.
    This allows us to be the central source of auth information/connected teams.
    We synchronize everything on requests from the API, so that we don't have to
    worry about stale data.

    @param request: Incoming request with auth information
    @return: WhoAmIResult
    """

    user, _ = request.auth
    return await WhoAmIResult.from_user(user)


@router.post("/v1/auth/api_key", response=str, tags=["auth"])
@permission(user_can_create_api_key)
async def create_api_key(request, api_key: ApiKeyIn) -> str:
    user, _ = request.auth
    api_key, _ = await create_api_key_for_user(user, key_name=api_key.name)
    return api_key


@router.get("/v1/api_keys", response=typing.List[ApiKeyOut], tags=["auth"])
@permission(user_can_get_api_keys)
async def get_api_keys(request, limit: int = 100) -> typing.List[ApiKeyOut]:
    """Gets the API keys for the current user.
    All users can get this. Note that these are not in plaintext.

    @param request: Django request
    @param limit: Limit of API keys to return
    @return:
    """
    user, _ = request.auth
    # TODO -- ensure we're index on user email...
    return [
        ApiKeyOut.from_orm(obj)
        async for obj in APIKey.objects.filter(user__id=user.id).order_by("-created_at")
    ]


@router.delete("/v1/api_key/{api_key_id}", response=None, tags=["auth"])
@permission(user_can_delete_api_key)
async def delete_api_key(request, api_key_id: int) -> None:
    """Deletes an API key

    @param request: Django request
    @param api_key_id: ID of the API key to delete
    @return:
    """
    existing = await APIKey.objects.aget(id=api_key_id)
    await existing.adelete()
