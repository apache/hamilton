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

import dataclasses
from collections.abc import Collection, Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    TextIO,
)

try:
    import polars as pl
except ImportError as e:
    raise NotImplementedError("Polars is not installed.") from e


# for polars <0.16.0 we need to determine whether type_aliases exist.
has_alias = False
if hasattr(pl, "type_aliases"):
    has_alias = True

# for polars 0.18.0 we need to check what to do.
if has_alias and hasattr(pl.type_aliases, "CsvEncoding"):
    from polars.type_aliases import CsvEncoding
else:
    CsvEncoding = type

# import these types to make type hinting work
from polars.datatypes import DataType, DataTypeClass  # noqa: F401

from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader, DataSaver

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


@dataclasses.dataclass
class PolarsScanCSVReader(DataLoader):
    """Class specifically to handle loading CSV files with Polars.
    Should map to https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.read_csv.html
    """

    file: str | TextIO | BytesIO | Path | BinaryIO | bytes
    # kwargs:
    has_header: bool = True
    columns: Sequence[int] | Sequence[str] = None
    new_columns: Sequence[str] = None
    separator: str = ","
    comment_char: str = None
    quote_char: str = '"'
    skip_rows: int = 0
    dtypes: Mapping[str, Any] | Sequence[Any] = None
    null_values: str | Sequence[str] | dict[str, str] = None
    missing_utf8_is_empty_string: bool = False
    ignore_errors: bool = False
    try_parse_dates: bool = False
    n_threads: int = None
    infer_schema_length: int = 100
    batch_size: int = 8192
    n_rows: int = None
    encoding: CsvEncoding | str = "utf8"
    low_memory: bool = False
    rechunk: bool = True
    use_pyarrow: bool = False
    storage_options: dict[str, Any] = None
    skip_rows_after_header: int = 0
    row_count_name: str = None
    row_count_offset: int = 0
    eol_char: str = "\n"
    raise_if_empty: bool = True

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.has_header is not None:
            kwargs["has_header"] = self.has_header
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.new_columns is not None:
            kwargs["new_columns"] = self.new_columns
        if self.separator is not None:
            kwargs["separator"] = self.separator
        if self.comment_char is not None:
            kwargs["comment_char"] = self.comment_char
        if self.quote_char is not None:
            kwargs["quote_char"] = self.quote_char
        if self.skip_rows is not None:
            kwargs["skip_rows"] = self.skip_rows
        if self.dtypes is not None:
            kwargs["dtypes"] = self.dtypes
        if self.null_values is not None:
            kwargs["null_values"] = self.null_values
        if self.missing_utf8_is_empty_string is not None:
            kwargs["missing_utf8_is_empty_string"] = self.missing_utf8_is_empty_string
        if self.ignore_errors is not None:
            kwargs["ignore_errors"] = self.ignore_errors
        if self.try_parse_dates is not None:
            kwargs["try_parse_dates"] = self.try_parse_dates
        if self.n_threads is not None:
            kwargs["n_threads"] = self.n_threads
        if self.infer_schema_length is not None:
            kwargs["infer_schema_length"] = self.infer_schema_length
        if self.n_rows is not None:
            kwargs["n_rows"] = self.n_rows
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.low_memory is not None:
            kwargs["low_memory"] = self.low_memory
        if self.rechunk is not None:
            kwargs["rechunk"] = self.rechunk
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.skip_rows_after_header is not None:
            kwargs["skip_rows_after_header"] = self.skip_rows_after_header
        if self.row_count_name is not None:
            kwargs["row_count_name"] = self.row_count_name
        if self.row_count_offset is not None:
            kwargs["row_count_offset"] = self.row_count_offset
        if self.eol_char is not None:
            kwargs["eol_char"] = self.eol_char
        if self.raise_if_empty is not None:
            kwargs["raise_if_empty"] = self.raise_if_empty
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pl.scan_csv(self.file, **self._get_loading_kwargs())

        metadata = utils.get_file_and_dataframe_metadata(self.file, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class PolarsSinkCSVWriter(DataSaver):
    """Class to handle sinking a Polars LazyFrame to a CSV file using streaming.

    Calls LazyFrame.sink_csv() directly, avoiding collect() for better performance.
    Should map to https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.sink_csv.html

    Note: ``lazy=True`` is intentionally excluded because ``save_data()`` expects
    the file to exist immediately after the call returns.
    """

    file: str | Path
    # kwargs:
    include_bom: bool | None = None
    compression: str | None = None
    compression_level: int | None = None
    check_extension: bool | None = None
    include_header: bool = True
    separator: str = ","
    line_terminator: str = "\n"
    quote_char: str = '"'
    batch_size: int = 1024
    datetime_format: str | None = None
    date_format: str | None = None
    time_format: str | None = None
    float_scientific: bool | None = None
    float_precision: int | None = None
    decimal_comma: bool | None = None
    null_value: str | None = None
    quote_style: Any = None
    maintain_order: bool = True
    storage_options: dict[str, Any] | None = None
    credential_provider: Any = None
    retries: int | None = None
    sync_on_close: Any = None
    mkdir: bool | None = None
    engine: Any = None
    optimizations: Any = None
    extra_kwargs: dict[str, Any] | None = None

    def _get_saving_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.include_bom is not None:
            kwargs["include_bom"] = self.include_bom
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.compression_level is not None:
            kwargs["compression_level"] = self.compression_level
        if self.check_extension is not None:
            kwargs["check_extension"] = self.check_extension
        if self.include_header is not None:
            kwargs["include_header"] = self.include_header
        if self.separator is not None:
            kwargs["separator"] = self.separator
        if self.line_terminator is not None:
            kwargs["line_terminator"] = self.line_terminator
        if self.quote_char is not None:
            kwargs["quote_char"] = self.quote_char
        if self.batch_size is not None:
            kwargs["batch_size"] = self.batch_size
        if self.datetime_format is not None:
            kwargs["datetime_format"] = self.datetime_format
        if self.date_format is not None:
            kwargs["date_format"] = self.date_format
        if self.time_format is not None:
            kwargs["time_format"] = self.time_format
        if self.float_scientific is not None:
            kwargs["float_scientific"] = self.float_scientific
        if self.float_precision is not None:
            kwargs["float_precision"] = self.float_precision
        if self.decimal_comma is not None:
            kwargs["decimal_comma"] = self.decimal_comma
        if self.null_value is not None:
            kwargs["null_value"] = self.null_value
        if self.quote_style is not None:
            kwargs["quote_style"] = self.quote_style
        if self.maintain_order is not None:
            kwargs["maintain_order"] = self.maintain_order
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.credential_provider is not None:
            kwargs["credential_provider"] = self.credential_provider
        if self.retries is not None:
            kwargs["retries"] = self.retries
        if self.sync_on_close is not None:
            kwargs["sync_on_close"] = self.sync_on_close
        if self.mkdir is not None:
            kwargs["mkdir"] = self.mkdir
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.optimizations is not None:
            kwargs["optimizations"] = self.optimizations
        if self.extra_kwargs is not None:
            if self.extra_kwargs.get("lazy", False):
                raise ValueError("lazy=True is incompatible with synchronous data savers.")
            kwargs.update(self.extra_kwargs)
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def save_data(self, data: pl.LazyFrame) -> dict[str, Any]:
        data.sink_csv(self.file, **self._get_saving_kwargs())
        return utils.get_file_metadata(self.file)

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class PolarsScanParquetReader(DataLoader):
    """Class specifically to handle loading parquet files with polars
    Should map to https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.read_parquet.html
    """

    file: str | TextIO | BytesIO | Path | BinaryIO | bytes
    # kwargs:
    columns: list[int] | list[str] = None
    n_rows: int = None
    use_pyarrow: bool = False
    memory_map: bool = True
    storage_options: dict[str, Any] = None
    parallel: Any = "auto"
    row_count_name: str = None
    row_count_offset: int = 0
    low_memory: bool = False
    use_statistics: bool = True
    rechunk: bool = True

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.n_rows is not None:
            kwargs["n_rows"] = self.n_rows
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.parallel is not None:
            kwargs["parallel"] = self.parallel
        if self.row_count_name is not None:
            kwargs["row_count_name"] = self.row_count_name
        if self.row_count_offset is not None:
            kwargs["row_count_offset"] = self.row_count_offset
        if self.low_memory is not None:
            kwargs["low_memory"] = self.low_memory
        if self.use_statistics is not None:
            kwargs["use_statistics"] = self.use_statistics
        if self.rechunk is not None:
            kwargs["rechunk"] = self.rechunk
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pl.scan_parquet(self.file, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.file, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "parquet"


@dataclasses.dataclass
class PolarsSinkParquetWriter(DataSaver):
    """Class to handle sinking a Polars LazyFrame to a Parquet file using streaming.

    Calls LazyFrame.sink_parquet() directly, avoiding collect() for better performance.
    Should map to https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.sink_parquet.html

    Note: ``lazy=True`` is intentionally excluded because ``save_data()`` expects
    the file to exist immediately after the call returns.
    """

    file: str | Path
    # kwargs:
    compression: str = "zstd"
    compression_level: int | None = None
    statistics: bool | str | dict[str, bool] = True
    row_group_size: int | None = None
    data_page_size: int | None = None
    maintain_order: bool = True
    storage_options: dict[str, Any] | None = None
    credential_provider: Any = None
    retries: int | None = None
    sync_on_close: Any = None
    metadata: Any = None
    arrow_schema: Any = None
    mkdir: bool | None = None
    engine: Any = None
    optimizations: Any = None
    extra_kwargs: dict[str, Any] | None = None

    def _get_saving_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.compression_level is not None:
            kwargs["compression_level"] = self.compression_level
        if self.statistics is not None:
            kwargs["statistics"] = self.statistics
        if self.row_group_size is not None:
            kwargs["row_group_size"] = self.row_group_size
        if self.data_page_size is not None:
            kwargs["data_page_size"] = self.data_page_size
        if self.maintain_order is not None:
            kwargs["maintain_order"] = self.maintain_order
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.credential_provider is not None:
            kwargs["credential_provider"] = self.credential_provider
        if self.retries is not None:
            kwargs["retries"] = self.retries
        if self.sync_on_close is not None:
            kwargs["sync_on_close"] = self.sync_on_close
        if self.metadata is not None:
            kwargs["metadata"] = self.metadata
        if self.arrow_schema is not None:
            kwargs["arrow_schema"] = self.arrow_schema
        if self.mkdir is not None:
            kwargs["mkdir"] = self.mkdir
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.optimizations is not None:
            kwargs["optimizations"] = self.optimizations
        if self.extra_kwargs is not None:
            if self.extra_kwargs.get("lazy", False):
                raise ValueError("lazy=True is incompatible with synchronous data savers.")
            kwargs.update(self.extra_kwargs)
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def save_data(self, data: pl.LazyFrame) -> dict[str, Any]:
        data.sink_parquet(self.file, **self._get_saving_kwargs())
        return utils.get_file_metadata(self.file)

    @classmethod
    def name(cls) -> str:
        return "parquet"


@dataclasses.dataclass
class PolarsScanFeatherReader(DataLoader):
    """
    Class specifically to handle loading Feather/Arrow IPC files with Polars.
    Should map to https://pola-rs.github.io/polars/py-polars/html/reference/api/polars.read_ipc.html
    """

    source: str | BinaryIO | BytesIO | Path | bytes
    # kwargs:
    columns: list[str] | list[int] | None = None
    n_rows: int | None = None
    use_pyarrow: bool = False
    memory_map: bool = True
    storage_options: dict[str, Any] | None = None
    row_count_name: str | None = None
    row_count_offset: int = 0
    rechunk: bool = True

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.n_rows is not None:
            kwargs["n_rows"] = self.n_rows
        if self.memory_map is not None:
            kwargs["memory_map"] = self.memory_map
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.row_count_name is not None:
            kwargs["row_count_name"] = self.row_count_name
        if self.row_count_offset is not None:
            kwargs["row_count_offset"] = self.row_count_offset
        if self.rechunk is not None:
            kwargs["rechunk"] = self.rechunk
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pl.scan_ipc(self.source, **self._get_loading_kwargs())
        metadata = utils.get_file_metadata(self.source)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "feather"


@dataclasses.dataclass
class PolarsSinkFeatherWriter(DataSaver):
    """Class to handle sinking a Polars LazyFrame to an IPC/Feather file using streaming.

    Calls LazyFrame.sink_ipc() directly, avoiding collect() for better performance.
    Should map to https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.sink_ipc.html

    Note: ``lazy=True`` is intentionally excluded because ``save_data()`` expects
    the file to exist immediately after the call returns.
    """

    file: str | Path
    # kwargs:
    compression: str | None = None
    compat_level: Any = None
    record_batch_size: int | None = None
    maintain_order: bool = True
    storage_options: dict[str, Any] | None = None
    credential_provider: Any = None
    retries: int | None = None
    sync_on_close: Any = None
    mkdir: bool | None = None
    engine: Any = None
    optimizations: Any = None
    extra_kwargs: dict[str, Any] | None = None

    def _get_saving_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.compat_level is not None:
            kwargs["compat_level"] = self.compat_level
        if self.record_batch_size is not None:
            kwargs["record_batch_size"] = self.record_batch_size
        if self.maintain_order is not None:
            kwargs["maintain_order"] = self.maintain_order
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.credential_provider is not None:
            kwargs["credential_provider"] = self.credential_provider
        if self.retries is not None:
            kwargs["retries"] = self.retries
        if self.sync_on_close is not None:
            kwargs["sync_on_close"] = self.sync_on_close
        if self.mkdir is not None:
            kwargs["mkdir"] = self.mkdir
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.optimizations is not None:
            kwargs["optimizations"] = self.optimizations
        if self.extra_kwargs is not None:
            if self.extra_kwargs.get("lazy", False):
                raise ValueError("lazy=True is incompatible with synchronous data savers.")
            kwargs.update(self.extra_kwargs)
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def save_data(self, data: pl.LazyFrame) -> dict[str, Any]:
        data.sink_ipc(self.file, **self._get_saving_kwargs())
        return utils.get_file_metadata(self.file)

    @classmethod
    def name(cls) -> str:
        return "feather"


@dataclasses.dataclass
class PolarsSinkNDJSONWriter(DataSaver):
    """Class to handle sinking a Polars LazyFrame to an NDJSON file using streaming.

    Calls LazyFrame.sink_ndjson() directly, avoiding collect() for better performance.
    Should map to https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.sink_ndjson.html

    Note: ``lazy=True`` is intentionally excluded because ``save_data()`` expects
    the file to exist immediately after the call returns.
    """

    file: str | Path
    # kwargs:
    compression: str | None = None
    compression_level: int | None = None
    check_extension: bool | None = None
    maintain_order: bool = True
    storage_options: dict[str, Any] | None = None
    credential_provider: Any = None
    retries: int | None = None
    sync_on_close: Any = None
    mkdir: bool | None = None
    engine: Any = None
    optimizations: Any = None
    extra_kwargs: dict[str, Any] | None = None

    def _get_saving_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.compression_level is not None:
            kwargs["compression_level"] = self.compression_level
        if self.check_extension is not None:
            kwargs["check_extension"] = self.check_extension
        if self.maintain_order is not None:
            kwargs["maintain_order"] = self.maintain_order
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.credential_provider is not None:
            kwargs["credential_provider"] = self.credential_provider
        if self.retries is not None:
            kwargs["retries"] = self.retries
        if self.sync_on_close is not None:
            kwargs["sync_on_close"] = self.sync_on_close
        if self.mkdir is not None:
            kwargs["mkdir"] = self.mkdir
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.optimizations is not None:
            kwargs["optimizations"] = self.optimizations
        if self.extra_kwargs is not None:
            if self.extra_kwargs.get("lazy", False):
                raise ValueError("lazy=True is incompatible with synchronous data savers.")
            kwargs.update(self.extra_kwargs)
        return kwargs

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def save_data(self, data: pl.LazyFrame) -> dict[str, Any]:
        data.sink_ndjson(self.file, **self._get_saving_kwargs())
        return utils.get_file_metadata(self.file)

    @classmethod
    def name(cls) -> str:
        return "ndjson"


def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [
        PolarsScanCSVReader,
        PolarsSinkCSVWriter,
        PolarsScanParquetReader,
        PolarsSinkParquetWriter,
        PolarsScanFeatherReader,
        PolarsSinkFeatherWriter,
        PolarsSinkNDJSONWriter,
    ]:
        registry.register_adapter(loader)


register_data_loaders()
