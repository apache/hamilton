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

"""This module exists so that people can download dataflows without the sf-hamilton-contrib package.

It will get clobbered when sf-hamilton-contrib is installed, which is good.
"""

import logging
from contextlib import contextmanager

__version__ = "__unknown__"  # this will be overwritten once sf-hamilton-contrib is installed.

from hamilton import telemetry


@contextmanager
def catch_import_errors(module_name: str, file_location: str, logger: logging.Logger):
    try:
        # Yield control to the inner block which will have the import statements.
        yield
        # After all imports succeed send telemetry
        if "." in module_name:
            telemetry.create_and_send_contrib_use(module_name, __version__)
        else:
            # we are importing it dynamically thus a "package" isn't present so file_location has the info.
            telemetry.create_and_send_contrib_use(file_location, __version__)
    except ImportError as e:
        location = file_location[: file_location.rfind("/")]
        logger.error("ImportError: %s", e)
        logger.error(
            "Please install the required packages. Options:\n"
            f"(1): with `pip install -r {location}/requirements.txt`\n"
        )
        raise e
