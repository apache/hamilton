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

import sys

from hamilton import telemetry

# disable telemetry for all tests!
telemetry.disable_telemetry()

# Skip tests that require packages not yet available on Python 3.14
collect_ignore = []
if sys.version_info >= (3, 14):
    collect_ignore.extend(
        [
            # ray - no Python 3.14 support yet
            "test_h_ray.py",
            "test_parse_ray_remote_options_from_tags.py",
        ]
    )
