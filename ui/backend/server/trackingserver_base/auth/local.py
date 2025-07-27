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
from trackingserver_base.auth.sync import ensure_user_only_part_of_orgs

logger = logging.getLogger(__name__)


class LocalAPIAuthenticator(HttpAuthBase):
    """This is a local API authenticator for the Hamilton UI. This is not
    secure and should not be used in production outside of a very specific VPN context in which
    the team has shared global access."""

    def __init__(self, global_key: Optional[str] = None):
        self.global_key = global_key

    async def __call__(self, request: HttpRequest) -> Optional[Tuple[User, List[Team]]]:
        """This is an authentication client for local mode. It will ensure a user exists with
        the appropriate username.
        """
        username = request.headers.get("x-api-user")
        key = request.headers.get("x-api-key", None)
        return await self.ensure(username, key)

    async def ensure(self, username: str, key: str):
        if self.global_key is not None:
            if key is None or (key[0:200] != self.global_key[0:200]):
                return None
        try:
            user = await User.objects.aget(email=username)
        except User.DoesNotExist:
            logger.warning(f"Creating new user {username} for local mode")
            user = User(
                first_name=username.split("@")[0],
                last_name="local account",  # TODO -- get the actual last name
                email=username,
            )
            await user.asave()

            public = await Team.objects.aget(name="Public")
            await ensure_user_only_part_of_orgs(user, [public])
            return user, [public]
        teams = [
            item.team
            async for item in UserTeamMembership.objects.filter(user=user)
            .all()
            .prefetch_related("team")
        ]
        return user, teams
