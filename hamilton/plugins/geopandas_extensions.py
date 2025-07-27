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

from typing import Any

try:
    import geopandas as gpd
except ImportError as e:
    raise NotImplementedError("geopandas is not installed.") from e

from hamilton import registry

DATAFRAME_TYPE = gpd.GeoDataFrame
COLUMN_TYPE = gpd.GeoSeries


@registry.get_column.register(gpd.GeoDataFrame)
def get_column_geopandas(df: gpd.GeoDataFrame, column_name: str) -> gpd.GeoSeries:
    return df[column_name]


@registry.fill_with_scalar.register(gpd.GeoDataFrame)
def fill_with_scalar_geopandas(
    df: gpd.GeoDataFrame, column_name: str, value: Any
) -> gpd.GeoDataFrame:
    df[column_name] = value
    return df


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("geopandas", DATAFRAME_TYPE, COLUMN_TYPE)


register_types()
