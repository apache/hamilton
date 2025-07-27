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

# Quick hack to make this a backwards compatible refactor
# This allows us to define everything within the function_modifiers directory, and just refer to that
# While maintaining old imports
import logging

from hamilton.function_modifiers.base import *  # noqa F403

logger = logging.getLogger(__name__)
logger.warning(
    "Import of this module is deprecated, and will be removed in a 2.0 release. In fact, "
    "this is not a public-facing API, so if you're hitting this message either we're internally "
    "importing the wrong one or you're doing something fancy. Either way, \n"
    "please replace with `from hamilton.function_modifiers import base as fm_base`."
)
