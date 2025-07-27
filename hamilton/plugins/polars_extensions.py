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
from typing import Any, Type

from packaging import version

from hamilton import registry

logger = logging.getLogger(__name__)

try:
    from xlsxwriter.workbook import Workbook
except ImportError:
    Workbook = Type

try:
    import polars as pl
except ImportError as e:
    raise NotImplementedError("Polars is not installed.") from e

pl_version = version.Version(pl.__version__)
if pl_version < version.Version("1.0.0"):
    from hamilton.plugins.polars_pre_1_0_0_extension import register_data_loaders

    logger.warning(
        "Using pre-1.0.0 Polars integration -- we will stop supporting this in Hamilton 2.0, so please upgrade your version of polars! "
        f"Current version: {pl_version}, minimum required version: 1.0.0."
    )
else:
    from hamilton.plugins.polars_post_1_0_0_extensions import register_data_loaders

register_data_loaders()

DATAFRAME_TYPE = pl.DataFrame
COLUMN_TYPE = pl.Series


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("polars", DATAFRAME_TYPE, COLUMN_TYPE)


@registry.get_column.register(pl.DataFrame)
def get_column_polars(df: pl.DataFrame, column_name: str) -> pl.Series:
    return df[column_name]


@registry.fill_with_scalar.register(pl.DataFrame)
def fill_with_scalar_polars(df: pl.DataFrame, column_name: str, scalar_value: Any) -> pl.DataFrame:
    if not isinstance(scalar_value, pl.Series):
        scalar_value = [scalar_value]
    return df.with_columns(pl.Series(name=column_name, values=scalar_value))


register_types()
