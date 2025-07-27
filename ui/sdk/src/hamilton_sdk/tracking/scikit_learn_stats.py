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

from typing import List

from hamilton_sdk.tracking import data_observation
from sklearn.base import BaseEstimator

"""Module that houses functions to compute statistics on numpy objects"""


@data_observation.compute_stats.register(BaseEstimator)
def get_estimator_params(result, *args, **kwargs) -> data_observation.ObservationType:
    """
    ref: https://scikit-learn.org/stable/auto_examples/miscellaneous/plot_display_object_visualization.html
    """
    return {
        "name": "Parameters",
        "observability_type": "dict",
        "observability_value": {
            "type": str(type(result)),
            "value": result.get_params(deep=True),
        },
        "observability_schema_version": "0.0.2",
    }


@data_observation.compute_additional_results.register(BaseEstimator)
def get_estimator_html(result, *args, **kwargs) -> List[data_observation.ObservationType]:
    return [
        {
            "name": "Components",
            "observability_type": "html",
            "observability_value": {"html": result._repr_html_inner()},  # get_params(deep=True),
            "observability_schema_version": "0.0.1",
        }
    ]
