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

import pandas as pd
from components import utils

from hamilton.function_modifiers import config


@config.when(mode="batch")
def age_mean__batch(age: pd.Series) -> float:
    """Simple aggregation of age data."""
    return age.mean()


@config.when(mode="batch")
def age_stddev__batch(age: pd.Series) -> float:
    """Simple aggregation of age data."""
    return age.std()


@config.when(mode="online")
def age_mean__online() -> float:
    """Load the previously computed aggregation data"""
    return utils.query_scalar("age_mean")


@config.when(mode="online")
def age_stddev__online() -> float:
    """Load the previously computed aggregation data"""
    return utils.query_scalar("age_stddev")


@config.when(mode="streaming")
def age_mean__streaming() -> float:
    """Load the previously computed aggregation data.

    Note: this could be computed by the streaming system if it supports
    stateful aggregation. However, for this example it doesn't make sense
    so we don't show it.
    """
    return utils.query_scalar("age_mean")


@config.when(mode="streaming")
def age_stddev__streaming() -> float:
    """Load the previously computed aggregation data.
    Note: this could be computed by the streaming system if it supports
    stateful aggregation. However, for this example it doesn't make sense
    so we don't show it.
    """
    return utils.query_scalar("age_stddev")
