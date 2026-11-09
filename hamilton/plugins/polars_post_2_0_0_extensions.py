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

"""Polars >= 2.0.0 data loaders. These reuse the post-1.0.0 adapters, and subclass its CSV, Parquet
and Feather readers to pass on their fields under the argument names polars 2.0.0 uses. The readers
keep the post-1.0.0 fields. Those polars 2.0.0 removed default to None and warn when set, except
`rechunk`, which the readers apply to the loaded frame."""

import dataclasses
import warnings
from collections.abc import Iterable
from typing import Any

from hamilton import registry
from hamilton.io.data_adapters import DataLoader
from hamilton.plugins import polars_post_1_0_0_extensions as post_1
from hamilton.plugins.polars_post_1_0_0_extensions import (
    DATAFRAME_TYPE,
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsCSVWriter,
    PolarsDatabaseReader,
    PolarsDatabaseWriter,
    PolarsFeatherWriter,
    PolarsJSONReader,
    PolarsJSONWriter,
    PolarsNDJSONReader,
    PolarsNDJSONWriter,
    PolarsParquetWriter,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)

# Reader arguments polars renamed; polars 2.0.0 accepts only the new names.
_RENAMED_ARGUMENTS = {
    "comment_char": "comment_prefix",
    "dtypes": "schema_overrides",
    "row_count_name": "row_index_name",
    "row_count_offset": "row_index_offset",
}


def _to_polars_2_kwargs(kwargs: dict[str, Any], removed: Iterable[str]) -> dict[str, Any]:
    """Translates the keyword arguments of a polars < 2.0.0 reader for polars >= 2.0.0.

    Renamed arguments get their new names, ``missing_utf8_is_empty_string`` becomes its inverse
    ``empty_string_is_null``, and the arguments in ``removed`` are left out.
    """
    kwargs = {_RENAMED_ARGUMENTS.get(key, key): value for key, value in kwargs.items()}
    if "missing_utf8_is_empty_string" in kwargs:
        kwargs["empty_string_is_null"] = not kwargs.pop("missing_utf8_is_empty_string")
    for name in removed:
        kwargs.pop(name, None)
    return kwargs


def _warn_ignored_fields(reader: DataLoader, fields: Iterable[str]) -> None:
    """Warns about each of ``fields`` that ``reader`` sets, since polars >= 2.0.0 ignores them.

    Call it from the reader's ``__post_init__``, so the warning points at the line that built it.
    """
    for name in fields:
        if getattr(reader, name) is not None:
            warnings.warn(
                f"{type(reader).__name__}.{name} has no effect with polars>=2.0.0 and is ignored.",
                stacklevel=4,
            )


@dataclasses.dataclass
class PolarsCSVReader(post_1.PolarsCSVReader):
    """Class specifically to handle loading CSV files with Polars.
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.read_csv.html

    polars 2.0.0 removed `n_threads` and `batch_size`, so setting either warns and has no effect.
    `rechunk` is applied to the loaded frame.
    """

    n_threads: int | None = None
    batch_size: int | None = None

    def __post_init__(self):
        _warn_ignored_fields(self, ("n_threads", "batch_size"))

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(
            super()._get_loading_kwargs(), ("n_threads", "batch_size", "rechunk")
        )

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df, metadata = super().load_data(type_)
        return (df.rechunk() if self.rechunk else df), metadata


@dataclasses.dataclass
class PolarsParquetReader(post_1.PolarsParquetReader):
    """Class specifically to handle loading parquet files with polars
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.read_parquet.html

    `rechunk` is applied to the loaded frame, since polars 2.0.0 removed the argument.
    """

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(super()._get_loading_kwargs(), ("rechunk",))

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df, metadata = super().load_data(type_)
        return (df.rechunk() if self.rechunk else df), metadata


@dataclasses.dataclass
class PolarsFeatherReader(post_1.PolarsFeatherReader):
    """
    Class specifically to handle loading Feather/Arrow IPC files with Polars.
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.read_ipc.html

    polars 2.0.0 removed `memory_map`, so setting it warns and has no effect. `rechunk` is applied
    to the loaded frame.
    """

    memory_map: bool | None = None

    def __post_init__(self):
        _warn_ignored_fields(self, ("memory_map",))

    def _get_loading_kwargs(self):
        return _to_polars_2_kwargs(super()._get_loading_kwargs(), ("memory_map", "rechunk"))

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df, metadata = super().load_data(type_)
        return (df.rechunk() if self.rechunk else df), metadata


def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [
        PolarsCSVReader,
        PolarsCSVWriter,
        PolarsParquetReader,
        PolarsParquetWriter,
        PolarsFeatherReader,
        PolarsFeatherWriter,
        PolarsAvroReader,
        PolarsAvroWriter,
        PolarsJSONReader,
        PolarsJSONWriter,
        PolarsNDJSONReader,
        PolarsNDJSONWriter,
        PolarsDatabaseReader,
        PolarsDatabaseWriter,
        PolarsSpreadsheetReader,
        PolarsSpreadsheetWriter,
    ]:
        registry.register_adapter(loader)
