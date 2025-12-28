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

import configparser
from hamilton_sdk.tracking import constants


def test__convert_to_type():
    # using configparser to make it more realistic
    config = configparser.ConfigParser()
    config["SDK_CONSTANTS"] = {
        "CAPTURE_DATA_STATISTICS": "true",
        "MAX_LIST_LENGTH_CAPTURE": "5",
        "MAX_DICT_LENGTH_CAPTURE": "10",
        "SOMETHING_ELSE": "11.0",
        "Another_thing": "1asdfasdf",
    }
    assert constants._convert_to_type(config["SDK_CONSTANTS"]["CAPTURE_DATA_STATISTICS"]) is True
    assert constants._convert_to_type(config["SDK_CONSTANTS"]["MAX_LIST_LENGTH_CAPTURE"]) == 5
    assert constants._convert_to_type(config["SDK_CONSTANTS"]["MAX_DICT_LENGTH_CAPTURE"]) == 10
    assert constants._convert_to_type(config["SDK_CONSTANTS"]["SOMETHING_ELSE"]) == 11.0
    assert constants._convert_to_type(config["SDK_CONSTANTS"]["Another_thing"]) == "1asdfasdf"
    o = object()
    assert constants._convert_to_type(o) == o
