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
from contextlib import contextmanager

try:
    from .version import VERSION as __version__  # noqa: F401
except ImportError:
    from version import VERSION as __version__  # noqa: F401

from hamilton import telemetry


def track(module_name: str):
    """Function to call to track module usage."""
    if hasattr(telemetry, "create_and_send_contrib_use"):  # makes sure Hamilton version is fine.
        telemetry.create_and_send_contrib_use(module_name, __version__)


@contextmanager
def catch_import_errors(module_name: str, file_location: str, logger: logging.Logger):
    try:
        # Yield control to the inner block which will have the import statements.
        yield
        # After all imports succeed send telemetry
        track(module_name)
    except ImportError as e:
        location = file_location[: file_location.rfind("/")]
        logger.error("ImportError: %s", e)
        logger.error(
            "Please install the required packages. Options:\n"
            f"(1): with `pip install -r {location}/requirements.txt`\n"
        )
        raise e
