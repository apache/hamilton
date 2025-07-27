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

"""This module contains constants for tracking.

We then override these by:
1. Looking for a configuration file and taking the section under `SDK_CONSTANTS`.
2. Via environment variables. They should be prefixed with `HAMILTON_`.
3. Lastly folks can manually adjust these values directly by importing the module and changing the value.

Note: This module cannot import other Hamilton modules.
"""

import configparser
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# The following are the default values for the tracking client
CAPTURE_DATA_STATISTICS = True
MAX_LIST_LENGTH_CAPTURE = 50
MAX_DICT_LENGTH_CAPTURE = 100

# Check for configuration file
# TODO -- add configuration file support
DEFAULT_CONFIG_URI = os.environ.get("HAMILTON_CONFIG_URI", "~/.hamilton.conf")
DEFAULT_CONFIG_LOCATION = os.path.expanduser(DEFAULT_CONFIG_URI)


def _load_config(config_location: str) -> configparser.ConfigParser:
    """Pulls config if it exists.

    :param config_location: location of the config file.
    """
    config = configparser.ConfigParser()
    try:
        with open(config_location) as f:
            config.read_file(f)
    except Exception:
        pass

    return config


_constant_values = globals()
file_config = _load_config(DEFAULT_CONFIG_LOCATION)


def _convert_to_type(val_: str) -> Any:
    if not isinstance(val_, str):  # guard
        return val_
    if val_.isdigit():
        # convert to int
        val_ = int(val_)
    elif val_.lower() in {"true", "false"}:
        # convert to bool
        val_ = val_.lower() == "true"
    else:
        try:  # check if float
            val_ = float(val_)
        except ValueError:
            pass
    return val_


# loads from config file and overwrites
if "SDK_CONSTANTS" in file_config:
    for key, val in file_config["SDK_CONSTANTS"].items():
        upper_key = key.upper()
        if upper_key not in _constant_values:
            continue
        # convert from string to appropriate type
        val = _convert_to_type(val)
        # overwrite value
        _constant_values[upper_key] = val

# Check for environment variables & overwrites
# TODO automate this by pulling anything in with a prefix and checking
# globals here and updating them.
CAPTURE_DATA_STATISTICS = os.getenv("HAMILTON_CAPTURE_DATA_STATISTICS", CAPTURE_DATA_STATISTICS)
if isinstance(CAPTURE_DATA_STATISTICS, str):
    CAPTURE_DATA_STATISTICS = CAPTURE_DATA_STATISTICS.lower() == "true"
MAX_LIST_LENGTH_CAPTURE = int(
    os.getenv("HAMILTON_MAX_LIST_LENGTH_CAPTURE", MAX_LIST_LENGTH_CAPTURE)
)
MAX_DICT_LENGTH_CAPTURE = int(
    os.getenv("HAMILTON_MAX_DICT_LENGTH_CAPTURE", MAX_DICT_LENGTH_CAPTURE)
)
