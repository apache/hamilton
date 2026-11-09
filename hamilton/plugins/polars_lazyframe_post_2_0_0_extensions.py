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

"""Polars >= 2.0.0 LazyFrame data loaders. polars_lazyframe_extensions registers these instead of
the polars_lazyframe_pre_2_0_0_extensions readers, which they subclass to pass on their fields under
the argument names polars 2.0.0 uses. The fields stay the same; those polars 2.0.0 removed default to
None and warn when set."""

import dataclasses
from collections.abc import Sequence
from typing import Any

import polars as pl

from hamilton import registry
from hamilton.io import utils
from hamilton.plugins import polars_lazyframe_pre_2_0_0_extensions as pre_2
from hamilton.plugins.polars_post_2_0_0_extensions import _to_polars_2_kwargs, _warn_ignored_fields

DATAFRAME_TYPE = pl.LazyFrame


def _select_columns(
    df: pl.LazyFrame, columns: Sequence[int] | Sequence[str] | None, row_index_name: str | None
) -> pl.LazyFrame:
    """Selects ``columns`` after a scan, since the ``scan_*`` functions do not take ``columns``.

    Matches ``read_*(columns=...)``: a single name selects that column, column positions count
    from the file's columns (negative ones from its end), and the row index column, when there is
    one, stays first.
    """
    if columns is None:
        return df
    if isinstance(columns, str):
        columns = [columns]
    if all(isinstance(column, int) for column in columns):
        offset = 0 if row_index_name is None else 1
        selected = pl.nth(
            *(position + offset if position >= 0 else position for position in columns)
        )
    else:
        selected = pl.col(*columns)
    if row_index_name is None:
        return df.select(selected)
    return df.select(pl.col(row_index_name), selected)


@dataclasses.dataclass
class PolarsScanCSVReader(pre_2.PolarsScanCSVReader):
    """Class specifically to handle loading CSV files with Polars.
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.scan_csv.html

    `columns` is selected after the scan. `n_threads`, `batch_size` and `rechunk` have no effect,
    so setting any of them warns.
    """

    n_threads: int | None = None
    batch_size: int | None = None
    rechunk: bool | None = None

    def __post_init__(self):
        _warn_ignored_fields(self, ("n_threads", "batch_size", "rechunk"))

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(
            super()._get_loading_kwargs(), ("columns", "n_threads", "rechunk")
        )

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = _select_columns(
            pl.scan_csv(self.file, **self._get_loading_kwargs()), self.columns, self.row_count_name
        )
        metadata = utils.get_file_and_dataframe_metadata(self.file, df)
        return df, metadata


@dataclasses.dataclass
class PolarsScanParquetReader(pre_2.PolarsScanParquetReader):
    """Class specifically to handle loading parquet files with polars
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.scan_parquet.html

    `columns` is selected after the scan. `rechunk` has no effect with polars 2.0.0, so setting it
    warns.
    """

    rechunk: bool | None = None

    def __post_init__(self):
        _warn_ignored_fields(self, ("rechunk",))

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(super()._get_loading_kwargs(), ("columns", "rechunk"))

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = _select_columns(
            pl.scan_parquet(self.file, **self._get_loading_kwargs()),
            self.columns,
            self.row_count_name,
        )
        metadata = utils.get_file_and_dataframe_metadata(self.file, df)
        return df, metadata


@dataclasses.dataclass
class PolarsScanFeatherReader(pre_2.PolarsScanFeatherReader):
    """
    Class specifically to handle loading Feather/Arrow IPC files with Polars.
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.scan_ipc.html

    `columns` is selected after the scan. `memory_map` and `rechunk` have no effect with polars
    2.0.0, so setting either warns.
    """

    memory_map: bool | None = None
    rechunk: bool | None = None

    def __post_init__(self):
        _warn_ignored_fields(self, ("memory_map", "rechunk"))

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(
            super()._get_loading_kwargs(), ("columns", "memory_map", "rechunk")
        )

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = _select_columns(
            pl.scan_ipc(self.source, **self._get_loading_kwargs()),
            self.columns,
            self.row_count_name,
        )
        metadata = utils.get_file_metadata(self.source)
        return df, metadata


def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [
        PolarsScanCSVReader,
        PolarsScanParquetReader,
        PolarsScanFeatherReader,
    ]:
        registry.register_adapter(loader)
