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

"""
Telemetry has been removed from Hamilton.

This module is kept as a no-op stub for backwards compatibility,
so that any user code calling ``telemetry.disable_telemetry()``
will not break.
"""


def disable_telemetry():
    """No-op. Telemetry has been removed."""
    pass


def is_telemetry_enabled() -> bool:
    """Always returns False. Telemetry has been removed."""
    return False
