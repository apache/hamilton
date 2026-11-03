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

"""Polars >= 2.0.0 data loaders. These reuse the post-1.0.0 adapters and replace the ones whose
signatures changed in polars 2.0.0."""

import dataclasses
from collections.abc import Collection, Mapping, Sequence
from io import IOBase
from pathlib import Path
from typing import Any

import polars as pl

from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader
from hamilton.plugins.polars_post_1_0_0_extensions import (
    DATAFRAME_TYPE,
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsCSVReader,
    PolarsCSVWriter,
    PolarsDatabaseReader,
    PolarsDatabaseWriter,
    PolarsFeatherReader,
    PolarsFeatherWriter,
    PolarsJSONWriter,
    PolarsNDJSONWriter,
    PolarsParquetReader,
    PolarsParquetWriter,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)


@dataclasses.dataclass
class PolarsJSONReader(DataLoader):
    """
    Class specifically to handle loading JSON files with Polars.
    Should map to https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.read_json.html
    """

    source: str | Path | IOBase | bytes
    schema: Mapping[str, Any] | Sequence[str | tuple[str, Any]] | None = None
    schema_overrides: Mapping[str, Any] | Sequence[str | tuple[str, Any]] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.schema is not None:
            kwargs["schema"] = self.schema
        if self.schema_overrides is not None:
            kwargs["schema_overrides"] = self.schema_overrides
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pl.read_json(self.source, **self._get_loading_kwargs())
        metadata = utils.get_file_metadata(self.source)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "json"


@dataclasses.dataclass
class PolarsNDJSONReader(DataLoader):
    """
    Class specifically to handle loading NDJSON (newline-delimited JSON) files with Polars.
    Should map to https://docs.pola.rs/api/python/stable/reference/api/polars.read_ndjson.html
    """

    source: str | Path | IOBase | bytes
    schema: Mapping[str, Any] | Sequence[str | tuple[str, Any]] | None = None
    schema_overrides: Mapping[str, Any] | Sequence[str | tuple[str, Any]] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.schema is not None:
            kwargs["schema"] = self.schema
        if self.schema_overrides is not None:
            kwargs["schema_overrides"] = self.schema_overrides
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pl.read_ndjson(self.source, **self._get_loading_kwargs())
        metadata = utils.get_file_metadata(self.source)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "ndjson"


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
