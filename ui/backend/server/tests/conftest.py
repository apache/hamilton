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

import asyncio

import pytest
from trackingserver_base.auth.testing import TEST_USERS, TestAPIAuthenticator


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    # yield loop
    loop.close()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker, event_loop):
    with django_db_blocker.unblock():
        for username in TEST_USERS:
            event_loop.run_until_complete(TestAPIAuthenticator.ensure(username))
