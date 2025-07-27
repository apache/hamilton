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

from typing import Any, Dict

import pydantic
from hamilton_sdk.tracking import data_observation


@data_observation.compute_stats.register
def compute_stats_pydantic(
    result: pydantic.BaseModel, node_name: str, node_tags: dict
) -> Dict[str, Any]:
    if hasattr(result, "dump_model"):
        llm_result = result.dump_model()
    else:
        llm_result = result.dict()
    return {
        "observability_type": "dict",
        "observability_value": {
            "type": str(type(result)),
            "value": llm_result,
        },
        "observability_schema_version": "0.0.2",
    }
