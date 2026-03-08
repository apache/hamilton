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

from hamilton.dev_utils.deprecation import deprecated


@deprecated(
    warn_starting=(1, 89, 0),
    fail_starting=(2, 0, 0),
    use_this=None,
    explanation="Telemetry has been removed from Hamilton. This function is a no-op.",
    migration_guide="Simply remove any calls to `telemetry.disable_telemetry()`.",
)
def disable_telemetry():
    """No-op. Telemetry has been removed."""
    pass


@deprecated(
    warn_starting=(1, 89, 0),
    fail_starting=(2, 0, 0),
    use_this=None,
    explanation="Telemetry has been removed from Hamilton. This function always returns False.",
    migration_guide="Simply remove any calls to `telemetry.is_telemetry_enabled()`.",
)
def is_telemetry_enabled() -> bool:
    """Always returns False. Telemetry has been removed."""
    return False
