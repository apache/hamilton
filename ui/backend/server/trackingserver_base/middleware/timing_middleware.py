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

import time
from logging import getLogger

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

logger = getLogger(__name__)


class TimingMiddleware:
    async_capable = True
    sync_capable = False

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)
        self.iscoroutine = iscoroutinefunction(self.get_response)

    async def __call__(self, request):
        t0 = time.time()
        url = request.get_full_path()
        response = await self.get_response(request)
        t1 = time.time()
        is_sync = "Sync" if not self.iscoroutine else "Async"
        logger.warning(f"[{is_sync}] Request : {url} took {t1 - t0} seconds.")
        # Some logic ...
        return response
