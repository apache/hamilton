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

import numpy as np
import pandas as pd
from hamilton_sdk.tracking import data_observation, pandas_stats

"""Module that houses functions to compute statistics on numpy objects
Notes:
 - we should assume numpy v1.0+ so that we have a string type
"""


@data_observation.compute_stats.register
def compute_stats_numpy(result: np.ndarray, node_name: str, node_tags: dict) -> Dict[str, Any]:
    try:
        df = pd.DataFrame(result)  # hack - reuse pandas stuff
    except ValueError:
        return {
            "observability_type": "unsupported",
            "observability_value": {
                "unsupported_type": str(type(result)) + f" with dimensions {result.shape}",
                "action": "reach out to the DAGWorks team to add support for this type.",
            },
            "observability_schema_version": "0.0.1",
        }
    return {
        "observability_type": "dagworks_describe",
        "observability_value": pandas_stats._compute_stats(df),
        "observability_schema_version": "0.0.3",
    }
