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
import secrets
from typing import Tuple

from passlib.handlers.pbkdf2 import pbkdf2_sha256
from trackingserver_auth.models import APIKey, User

logger = logging.getLogger(__name__)

global_pepper = os.environ.get(
    "API_KEY_PEPPER", ""
)  # This is a global pepper that is used to salt the API keys


def get_salt(user: User) -> bytes:
    """Returns the salt for a user

    @param user: User to return the salt for a user.
    @return:
    """
    return bytes("".join([global_pepper, str(user.salt)]), "utf-8")


async def validate_api_key(user_email: str, api_key: str) -> bool:
    """Validates that an API key matches the user salt

    @param user_email:
    @param api_key:
    @return:
    """
    if api_key is None:
        return False
    user = await User.objects.aget(email=user_email)
    # TODO -- put the starts_with in the query
    api_key_candidates = [
        item
        async for item in APIKey.objects.filter(user=user)
        if api_key.startswith(item.key_start)
    ]
    for api_key_candidate in api_key_candidates:
        if not api_key_candidate.is_active:
            continue
        api_key = api_key[0:200]  # This is a quick way to avoid comparison/overflow security issues
        if pbkdf2_sha256.hash(api_key, salt=get_salt(user)) == api_key_candidate.hashed_key:
            return True
    return False


async def create_api_key_for_user(user: User, key_name: str) -> Tuple[str, APIKey]:
    """Creates an API key for the user. This is a one-way operation, so we can't
    recover the key once the reference is lost. That's OK -- they'll create another.

    @param user: User to create the API key for
    @param key_name: Name of the key
    @return: The generated key
    """
    generated_key = secrets.token_urlsafe(64)
    hashed_key = pbkdf2_sha256.hash(generated_key, salt=get_salt(user))
    api_key = APIKey(
        key_name=key_name,
        key_start=generated_key[0:5],
        hashed_key=hashed_key,
        user=user,
    )
    await api_key.asave()
    return generated_key, api_key
