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

from packaging import version

try:
    import polars as pl
except ImportError as e:
    raise NotImplementedError("Polars is not installed.") from e

from hamilton import registry

DATAFRAME_TYPE = pl.LazyFrame
COLUMN_TYPE = pl.Expr
# COLUMN_FRIENDLY_DF_TYPE = False


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("polars_lazyframe", DATAFRAME_TYPE, COLUMN_TYPE)


@registry.get_column.register(pl.LazyFrame)
def get_column_polars_lazyframe(df: pl.LazyFrame, column_name: str) -> pl.Expr:
    # TODO: figure out if we can validate this here already or need to wait to the end
    # when query.collect() resolves the lazy frame
    # df.collect_schema().names() gives a list of names but it can be expensive
    # https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.columns.html
    # https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.collect_schema.html#polars.LazyFrame.collect_schema
    return pl.col(column_name)


@registry.fill_with_scalar.register(pl.LazyFrame)
def fill_with_scalar_polars_lazyframe(
    df: pl.LazyFrame, column_name: str, scalar_value: Any
) -> pl.LazyFrame:
    if not isinstance(scalar_value, pl.Expr):
        scalar_value = pl.lit(scalar_value)
    return df.with_columns(scalar_value.alias(column_name))


register_types()

# The scan readers are imported here, rather than only registered, so that importing them from this
# module gives the readers registered for the installed polars.
if version.Version(pl.__version__) < version.Version("2.0.0"):
    from hamilton.plugins.polars_lazyframe_pre_2_0_0_extensions import (
        PolarsScanCSVReader,  # noqa: F401
        PolarsScanFeatherReader,  # noqa: F401
        PolarsScanParquetReader,  # noqa: F401
        register_data_loaders,
    )
else:
    from hamilton.plugins.polars_lazyframe_post_2_0_0_extensions import (
        PolarsScanCSVReader,  # noqa: F401
        PolarsScanFeatherReader,  # noqa: F401
        PolarsScanParquetReader,  # noqa: F401
        register_data_loaders,
    )

register_data_loaders()
