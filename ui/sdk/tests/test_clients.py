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
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from hamilton_sdk.api.clients import BasicAsynchronousHamiltonClient


def _make_client():
    return BasicAsynchronousHamiltonClient(
        api_key="test-key",
        username="test-user",
        h_api_url="http://localhost:8241",
    )


def _mock_session_with_status(status: int):
    """Build a mocked aiohttp.ClientSession() chain whose response
    .raise_for_status() raises ClientResponseError if status >= 400."""
    response = MagicMock()
    if status >= 400:
        response.raise_for_status.side_effect = aiohttp.ClientResponseError(
            request_info=MagicMock(),
            history=(),
            status=status,
            message=f"HTTP {status}",
        )
    else:
        response.raise_for_status.return_value = None

    put_cm = MagicMock()
    put_cm.__aenter__ = AsyncMock(return_value=response)
    put_cm.__aexit__ = AsyncMock(return_value=False)

    session = MagicMock()
    session.put.return_value = put_cm

    session_cm = MagicMock()
    session_cm.__aenter__ = AsyncMock(return_value=session)
    session_cm.__aexit__ = AsyncMock(return_value=False)
    return session_cm


def test_async_flush_re_raises_on_backend_error():
    """Regression: flush() used to catch requests.HTTPError (the wrong class
    for aiohttp) and swallowed errors via a `# zraise` tombstone. A non-2xx
    response from the backend must now propagate."""

    async def run():
        client = _make_client()
        batch = [{"dag_run_id": 1, "attributes": [], "task_updates": []}]
        with patch("aiohttp.ClientSession", return_value=_mock_session_with_status(500)):
            with pytest.raises(aiohttp.ClientResponseError):
                await client.flush(batch)

    asyncio.run(run())


def test_async_flush_succeeds_on_2xx():
    async def run():
        client = _make_client()
        batch = [{"dag_run_id": 1, "attributes": [], "task_updates": []}]
        with patch("aiohttp.ClientSession", return_value=_mock_session_with_status(200)):
            await client.flush(batch)

    asyncio.run(run())
