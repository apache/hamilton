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

import pytest
from trackingserver_base.auth.api_keys import create_api_key_for_user, validate_api_key

from tests.test_db_methods.utils import setup_sample_user_random


@pytest.mark.asyncio
async def test_create_api_key_for_user(db):
    user = await setup_sample_user_random()
    api_key, obj = await create_api_key_for_user(user, "foo_key")
    assert len(api_key) > 64
    return user, api_key


@pytest.mark.asyncio
async def test_validate_api_key_valid(db):
    user, api_key = await test_create_api_key_for_user(db)
    assert await validate_api_key(user.email, api_key)


@pytest.mark.asyncio
async def test_validate_api_key_invalid(db):
    user, api_key = await test_create_api_key_for_user(db)
    assert await validate_api_key(user.email, str(reversed(api_key))) is False
    assert await validate_api_key(user.email, "invalid_key") is False
    assert await validate_api_key(user.email, "very_long_invalid_key" * 100000) is False
