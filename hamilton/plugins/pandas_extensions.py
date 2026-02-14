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

import abc
import csv
import dataclasses
from collections.abc import Callable, Collection, Hashable, Iterator
from datetime import datetime
from io import BufferedReader, BytesIO, StringIO
from pathlib import Path
from typing import Any, TypeAlias

try:
    import pandas as pd
except ImportError as e:
    raise NotImplementedError("Pandas is not installed.") from e

from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

try:
    import fsspec
    import pyarrow.fs

    FILESYSTEM_TYPE = pyarrow.fs.FileSystem | fsspec.spec.AbstractFileSystem | None
except ImportError:
    FILESYSTEM_TYPE = type | None

from sqlite3 import Connection

from pandas._typing import NpDtype
from pandas.core.dtypes.dtypes import ExtensionDtype

from hamilton import registry
from hamilton.io import utils
from hamilton.io.data_adapters import DataLoader, DataSaver

DATAFRAME_TYPE = pd.DataFrame
COLUMN_TYPE = pd.Series

JSONSerializable: TypeAlias = str | float | bool | list | dict | None
IndexLabel: TypeAlias = Hashable | Iterator[Hashable] | None
Dtype: TypeAlias = ExtensionDtype | NpDtype


@registry.get_column.register(pd.DataFrame)
def get_column_pandas(df: pd.DataFrame, column_name: str) -> pd.Series:
    return df[column_name]


@registry.fill_with_scalar.register(pd.DataFrame)
def fill_with_scalar_pandas(df: pd.DataFrame, column_name: str, value: Any) -> pd.DataFrame:
    df[column_name] = value
    return df


def register_types():
    """Function to register the types for this extension."""
    registry.register_types("pandas", DATAFRAME_TYPE, COLUMN_TYPE)


register_types()


class DataFrameDataLoader(DataLoader, DataSaver, abc.ABC):
    """Base class for data loaders that saves/loads pandas dataframes.
    Note that these are currently grouped together, but this could change!
    We can change this as these are not part of the publicly exposed APIs.
    Rather, the fixed component is the keys (E.G. csv, feather, etc...) , which,
    when combined with types, correspond to a group of specific parameter. As such,
    the backwards-compatible invariance enables us to change the implementation
    (which classes), and so long as the set of parameters/load targets are compatible,
    we are good to go."""

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    @abc.abstractmethod
    def load_data(self, type_: type[DATAFRAME_TYPE]) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        pass

    @abc.abstractmethod
    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        pass


@dataclasses.dataclass
class PandasCSVReader(DataLoader):
    """
    Class that handles saving CSV files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    """

    # the filepath_or_buffer param will be changed to path for backwards compatibility
    path: str | Path | BytesIO | BufferedReader
    # kwargs
    sep: str | None = ","
    delimiter: str | None = None
    header: Sequence | int | Literal["infer"] | None = "infer"
    names: Sequence | None = None
    index_col: Hashable | Sequence | Literal[False] | None = None
    usecols: list[Hashable] | Callable | tuple | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    engine: Literal["c", "python", "pyarrow", "python-fwf"] | None = None
    converters: Mapping | None = None
    true_values: list | None = None
    false_values: list | None = None
    skipinitialspace: bool | None = False
    skiprows: list[int] | int | Callable[[Hashable], bool] | None = None
    skipfooter: int = 0
    nrows: int | None = None
    na_values: Hashable | Iterable | Mapping | None = None
    keep_default_na: bool = True
    na_filter: bool = True
    verbose: bool = False
    skip_blank_lines: bool = True
    parse_dates: bool | Sequence | None | None = False
    keep_date_col: bool = False
    date_format: str | None = None
    dayfirst: bool = False
    cache_dates: bool = True
    iterator: bool = False
    chunksize: int | None = None
    compression: (
        Literal["infer", "gzip", "bz2", "zip", "xz", "zstd", "tar"] | dict[str, Any] | None
    ) = "infer"
    thousands: str | None = None
    decimal: str = "."
    lineterminator: str | None = None
    quotechar: str | None = None
    quoting: int = 0
    doublequote: bool = True
    escapechar: str | None = None
    comment: str | None = None
    encoding: str = "utf-8"
    encoding_errors: (
        Literal["strict", "ignore", "replace", "backslashreplace", "surrogateescape"] | str
    ) = "strict"
    dialect: str | csv.Dialect | None = None
    on_bad_lines: Literal["error", "warn", "skip"] | Callable = "error"
    delim_whitespace: bool = False
    low_memory: bool = True
    memory_map: bool = False
    float_precision: Literal["high", "legacy", "round_trip"] | None = None
    storage_options: dict[str, Any] | None = None
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.sep is not None:
            kwargs["sep"] = self.sep
        if self.delimiter is not None:
            kwargs["delimiter"] = self.delimiter
        if self.header is not None:
            kwargs["header"] = self.header
        if self.names is not None:
            kwargs["names"] = self.names
        if self.index_col is not None:
            kwargs["index_col"] = self.index_col
        if self.usecols is not None:
            kwargs["usecols"] = self.usecols
        if self.dtype is not None:
            kwargs["dtype"] = self.dtype
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.converters is not None:
            kwargs["converters"] = self.converters
        if self.true_values is not None:
            kwargs["true_values"] = self.true_values
        if self.false_values is not None:
            kwargs["false_values"] = self.false_values
        if self.skipinitialspace is not None:
            kwargs["skipinitialspace"] = self.skipinitialspace
        if self.skiprows is not None:
            kwargs["skiprows"] = self.skiprows
        if self.nrows is not None:
            kwargs["nrows"] = self.nrows
        if self.na_values is not None:
            kwargs["na_values"] = self.na_values
        if self.keep_default_na is not None:
            kwargs["keep_default_na"] = self.keep_default_na
        if self.na_filter is not None:
            kwargs["na_filter"] = self.na_filter
        if pd.__version__ < "3.0" and self.verbose is not None:
            kwargs["verbose"] = self.verbose
        if self.skip_blank_lines is not None:
            kwargs["skip_blank_lines"] = self.skip_blank_lines
        if self.parse_dates is not None:
            kwargs["parse_dates"] = self.parse_dates
        if pd.__version__ < "3.0" and self.keep_date_col is not None:
            kwargs["keep_date_col"] = self.keep_date_col
        if self.date_format is not None:
            kwargs["date_format"] = self.date_format
        if self.dayfirst is not None:
            kwargs["dayfirst"] = self.dayfirst
        if self.cache_dates is not None:
            kwargs["cache_dates"] = self.cache_dates
        if self.iterator is not None:
            kwargs["iterator"] = self.iterator
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.thousands is not None:
            kwargs["thousands"] = self.thousands
        if self.lineterminator is not None:
            kwargs["lineterminator"] = self.lineterminator
        if self.quotechar is not None:
            kwargs["quotechar"] = self.quotechar
        if self.quoting is not None:
            kwargs["quoting"] = self.quoting
        if self.doublequote is not None:
            kwargs["doublequote"] = self.doublequote
        if self.escapechar is not None:
            kwargs["escapechar"] = self.escapechar
        if self.comment is not None:
            kwargs["comment"] = self.comment
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.encoding_errors is not None:
            kwargs["encoding_errors"] = self.encoding_errors
        if self.dialect is not None:
            kwargs["dialect"] = self.dialect
        if self.on_bad_lines is not None:
            kwargs["on_bad_lines"] = self.on_bad_lines
        if pd.__version__ < "3.0" and self.delim_whitespace is not None:
            kwargs["delim_whitespace"] = self.delim_whitespace
        if self.low_memory is not None:
            kwargs["low_memory"] = self.low_memory
        if self.memory_map is not None:
            kwargs["memory_map"] = self.memory_map
        if self.float_precision is not None:
            kwargs["float_precision"] = self.float_precision
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pd.read_csv(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class PandasCSVWriter(DataSaver):
    """Class that handles saving CSV files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    sep: str | None = ","
    na_rep: str = ""
    float_format: str | Callable | None = None
    columns: Sequence | None = None
    header: bool | list[str] | None = True
    index: bool | None = False
    index_label: IndexLabel | None = None
    mode: str = "w"
    encoding: str | None = None
    compression: (
        Literal["infer", "gzip", "bz2", "zip", "xz", "zstd", "tar"] | dict[str, Any] | None
    ) = "infer"
    quoting: int | None = None
    quotechar: str | None = '"'
    lineterminator: str | None = None
    chunksize: int | None = None
    date_format: str | None = None
    doublequote: bool = True
    escapechar: str | None = None
    decimal: str = "."
    errors: str = "strict"
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = {}
        if self.sep is not None:
            kwargs["sep"] = self.sep
        if self.na_rep is not None:
            kwargs["na_rep"] = self.na_rep
        if self.float_format is not None:
            kwargs["float_format"] = self.float_format
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.header is not None:
            kwargs["header"] = self.header
        if self.index is not None:
            kwargs["index"] = self.index
        if self.index_label is not None:
            kwargs["index_label"] = self.index_label
        if self.mode is not None:
            kwargs["mode"] = self.mode
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.quoting is not None:
            kwargs["quoting"] = self.quoting
        if self.quotechar is not None:
            kwargs["quotechar"] = self.quotechar
        if self.lineterminator is not None:
            kwargs["lineterminator"] = self.lineterminator
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.date_format is not None:
            kwargs["date_format"] = self.date_format
        if self.doublequote is not None:
            kwargs["doublequote"] = self.doublequote
        if self.escapechar is not None:
            kwargs["escapechar"] = self.escapechar
        if self.decimal is not None:
            kwargs["decimal"] = self.decimal
        if self.errors is not None:
            kwargs["errors"] = self.errors
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options

        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_csv(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "csv"


@dataclasses.dataclass
class PandasParquetReader(DataLoader):
    """Class that handles saving parquet files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_parquet.html#pandas.read_parquet
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    engine: Literal["auto", "pyarrow", "fastparquet"] = "auto"
    columns: list[str] | None = None
    storage_options: dict[str, Any] | None = None
    use_nullable_dtypes: bool = False
    dtype_backend: Literal["numpy_nullable", "pyarrow"] = "numpy_nullable"
    filesystem: str | None = None
    filters: list[tuple] | list[list[tuple]] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self):
        kwargs = {}
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if pd.__version__ < "2.0" and self.use_nullable_dtypes is not None:
            kwargs["use_nullable_dtypes"] = self.use_nullable_dtypes
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        if self.filesystem is not None:
            kwargs["filesystem"] = self.filesystem
        if self.filters is not None:
            kwargs["filters"] = self.filters

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the pickle
        df = pd.read_parquet(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "parquet"


@dataclasses.dataclass
class PandasParquetWriter(DataSaver):
    """Class that handles saving parquet files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_parquet.html#pandas.DataFrame.to_parquet
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    engine: Literal["auto", "pyarrow", "fastparquet"] = "auto"
    compression: str | None = "snappy"
    index: bool | None = None
    partition_cols: list[str] | None = None
    storage_options: dict[str, Any] | None = None
    extra_kwargs: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = {}
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.index is not None:
            kwargs["index"] = self.index
        if self.partition_cols is not None:
            kwargs["partition_cols"] = self.partition_cols
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.extra_kwargs is not None:
            kwargs.update(self.extra_kwargs)
        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_parquet(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "parquet"


@dataclasses.dataclass
class PandasPickleReader(DataLoader):
    """Class for loading/reading pickle files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_pickle.html#pandas.read_pickle
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader = None
    path: str | Path | BytesIO | BufferedReader = (
        None  # alias for `filepath_or_buffer` to keep reading/writing args symmetric.
    )
    # kwargs:
    compression: str | dict[str, Any] | None = "infer"
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        # Returns type for which data loader is available
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the pickle
        df = pd.read_pickle(self.filepath_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "pickle"

    def __post_init__(self):
        """As we're adding in a path alias for filepath_or_buffer, we need to ensure that
        we have backwards compatibility with the old parameter. That means that:
        1. Either filepath_or_buffer or path must be specified, not both
        2. If path is specified, filepath_or_buffer is set to path
        """
        if self.filepath_or_buffer is None and self.path is None:
            raise ValueError("Either filepath_or_buffer or path must be specified")
        elif self.filepath_or_buffer is not None and self.path is not None:
            raise ValueError("Only one of filepath_or_buffer or path must be specified")
        elif self.filepath_or_buffer is None:
            self.filepath_or_buffer = self.path


pickle_protocol_default = 5


@dataclasses.dataclass
class PandasPickleWriter(DataSaver):
    """Class that handles saving pickle files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_pickle.html#pandas.DataFrame.to_pickle
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs:
    compression: str | dict[str, Any] | None = "infer"
    protocol: int = pickle_protocol_default
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.protocol is not None:
            kwargs["protocol"] = self.protocol
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_pickle(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "pickle"


@dataclasses.dataclass
class PandasJsonReader(DataLoader):
    """Class specifically to handle loading JSON files/buffers with Pandas.

    Disclaimer: We're exposing all the *current* params from the Pandas read_json method.
    Some of these params may get deprecated or new params may be introduced. In the event that
    the params/kwargs below become outdated, please raise an issue or submit a pull request.

    Should map to https://pandas.pydata.org/docs/reference/api/pandas.read_json.html
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    chunksize: int | None = None
    compression: str | dict[str, Any] | None = "infer"
    convert_axes: bool | None = None
    convert_dates: bool | list[str] = True
    date_unit: str | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    dtype_backend: str | None = None
    encoding: str | None = None
    encoding_errors: str | None = "strict"
    engine: str = "ujson"
    keep_default_dates: bool = True
    lines: bool = False
    nrows: int | None = None
    orient: str | None = None
    precise_float: bool = False
    storage_options: dict[str, Any] | None = None
    typ: str = "frame"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.convert_axes is not None:
            kwargs["convert_axes"] = self.convert_axes
        if self.convert_dates is not None:
            kwargs["convert_dates"] = self.convert_dates
        if self.date_unit is not None:
            kwargs["date_unit"] = self.date_unit
        if self.dtype is not None:
            kwargs["dtype"] = self.dtype
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.encoding_errors is not None:
            kwargs["encoding_errors"] = self.encoding_errors
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.keep_default_dates is not None:
            kwargs["keep_default_dates"] = self.keep_default_dates
        if self.lines is not None:
            kwargs["lines"] = self.lines
        if self.nrows is not None:
            kwargs["nrows"] = self.nrows
        if self.orient is not None:
            kwargs["orient"] = self.orient
        if self.precise_float is not None:
            kwargs["precise_float"] = self.precise_float
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.typ is not None:
            kwargs["typ"] = self.typ
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pd.read_json(self.filepath_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "json"


@dataclasses.dataclass
class PandasJsonWriter(DataSaver):
    """Class specifically to handle saving JSON files/buffers with Pandas.

    Disclaimer: We're exposing all the *current* params from the Pandas DataFrame.to_json method.
    Some of these params may get deprecated or new params may be introduced. In the event that
    the params/kwargs below become outdated, please raise an issue or submit a pull request.

    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    compression: str = "infer"
    date_format: str = "epoch"
    date_unit: str = "ms"
    default_handler: Callable[[Any], JSONSerializable] | None = None
    double_precision: int = 10
    force_ascii: bool = True
    index: bool | None = None
    indent: int = 0
    lines: bool = False
    mode: str = "w"
    orient: str | None = None
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.date_format is not None:
            kwargs["date_format"] = self.date_format
        if self.date_unit is not None:
            kwargs["date_unit"] = self.date_unit
        if self.default_handler is not None:
            kwargs["default_handler"] = self.default_handler
        if self.double_precision is not None:
            kwargs["double_precision"] = self.double_precision
        if self.force_ascii is not None:
            kwargs["force_ascii"] = self.force_ascii
        if self.index is not None:
            kwargs["index"] = self.index
        if self.indent is not None:
            kwargs["indent"] = self.indent
        if self.lines is not False:
            kwargs["lines"] = self.lines
        if self.mode is not None:
            kwargs["mode"] = self.mode
        if self.orient is not None:
            kwargs["orient"] = self.orient
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_json(self.filepath_or_buffer, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, data)

    @classmethod
    def name(cls) -> str:
        return "json"


@dataclasses.dataclass
class PandasSqlReader(DataLoader):
    """Class specifically to handle loading SQL data using Pandas.

    Disclaimer: We're exposing all the *current* params from the Pandas read_sql method.
    Some of these params may get deprecated or new params may be introduced. In the event that
    the params/kwargs below become outdated, please raise an issue or submit a pull request.

    Should map to https://pandas.pydata.org/docs/reference/api/pandas.read_sql.html
    Requires optional Pandas dependencies. See https://pandas.pydata.org/docs/getting_started/install.html#sql-databases.
    """

    query_or_table: str
    db_connection: str | Connection  # can pass in SQLAlchemy engine/connection
    # kwarg
    chunksize: int | None = None
    coerce_float: bool = True
    columns: list[str] | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    dtype_backend: str | None = None
    index_col: str | list[str] | None = None
    params: list | tuple | dict | None = None
    parse_dates: list | dict | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.coerce_float is not None:
            kwargs["coerce_float"] = self.coerce_float
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.dtype is not None:
            kwargs["dtype"] = self.dtype
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        if self.index_col is not None:
            kwargs["index_col"] = self.index_col
        if self.params is not None:
            kwargs["params"] = self.params
        if self.parse_dates is not None:
            kwargs["parse_dates"] = self.parse_dates
        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        df = pd.read_sql(self.query_or_table, self.db_connection, **self._get_loading_kwargs())
        sql_metadata = utils.get_sql_metadata(self.query_or_table, df)
        df_metadata = utils.get_dataframe_metadata(df)
        return df, {**sql_metadata, **df_metadata}

    @classmethod
    def name(cls) -> str:
        return "sql"


@dataclasses.dataclass
class PandasSqlWriter(DataSaver):
    """Class specifically to handle saving DataFrames to SQL databases using Pandas.

    Disclaimer: We're exposing all the *current* params from the Pandas DataFrame.to_sql method.
    Some of these params may get deprecated or new params may be introduced. In the event that
    the params/kwargs below become outdated, please raise an issue or submit a pull request.

    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_sql.html
    Requires optional Pandas dependencies. See https://pandas.pydata.org/docs/getting_started/install.html#sql-databases.
    """

    table_name: str
    db_connection: Any  # can pass in SQLAlchemy engine/connection
    # kwargs
    chunksize: int | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    if_exists: str = "fail"
    index: bool = True
    index_label: IndexLabel | None = None
    method: str | Callable | None = None
    schema: str | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.dtype is not None:
            kwargs["dtype"] = self.dtype
        if self.if_exists is not None:
            kwargs["if_exists"] = self.if_exists
        if self.index is not None:
            kwargs["index"] = self.index
        if self.index_label is not None:
            kwargs["index_label"] = self.index_label
        if self.method is not None:
            kwargs["method"] = self.method
        if self.schema is not None:
            kwargs["schema"] = self.schema
        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        results = data.to_sql(self.table_name, self.db_connection, **self._get_saving_kwargs())
        sql_metadata = utils.get_sql_metadata(self.table_name, results)
        df_metadata = utils.get_dataframe_metadata(data)
        return {**sql_metadata, **df_metadata}

    @classmethod
    def name(cls) -> str:
        return "sql"


@dataclasses.dataclass
class PandasXmlReader(DataLoader):
    """Class for loading/reading xml files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_xml.html

    Requires `lxml`. See https://pandas.pydata.org/docs/getting_started/install.html#xml
    """

    path_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    xpath: str | None = "./*"
    namespace: dict[str, str] | None = None
    elems_only: bool | None = False
    attrs_only: bool | None = False
    names: list[str] | None = None
    dtype: dict[str, Any] | None = None
    converters: dict[int | str, Any] | None = None
    parse_dates: bool | list[int | str | list[list] | dict[str, list[int]]] = False
    encoding: str | None = "utf-8"
    parser: str = "lxml"
    stylesheet: str | Path | BytesIO | BufferedReader = None
    iterparse: dict[str, list[str]] | None = None
    compression: str | dict[str, Any] | None = "infer"
    storage_options: dict[str, Any] | None = None
    dtype_backend: str = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.xpath is not None:
            kwargs["xpath"] = self.xpath
        if self.namespace is not None:
            kwargs["namespace"] = self.namespace
        if self.elems_only is not None:
            kwargs["elems_only"] = self.elems_only
        if self.attrs_only is not None:
            kwargs["attrs_only"] = self.attrs_only
        if self.names is not None:
            kwargs["names"] = self.names
        if self.dtype is not None:
            kwargs["dtype"] = self.dtype
        if self.converters is not None:
            kwargs["converters"] = self.converters
        if self.parse_dates is not None:
            kwargs["parse_dates"] = self.parse_dates
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.parser is not None:
            kwargs["parser"] = self.parser
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.parser is not None:
            kwargs["parser"] = self.parser
        if self.stylesheet is not None:
            kwargs["stylesheet"] = self.stylesheet
        if self.iterparse is not None:
            kwargs["iterparse"] = self.iterparse
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        return kwargs

    def load_data(self, type: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the xml
        df = pd.read_xml(self.path_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "xml"


@dataclasses.dataclass
class PandasXmlWriter(DataSaver):
    """Class specifically to handle saving xml files/buffers with Pandas.
    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_xml.html

    Requires `lxml`. See https://pandas.pydata.org/docs/getting_started/install.html#xml.
    """

    path_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    index: bool = True
    root_name: str = "data"
    row_name: str = "row"
    na_rep: str | None = None
    attr_cols: list[str] | None = None
    elems_cols: list[str] | None = None
    namespaces: dict[str, str] | None = None
    prefix: str | None = None
    encoding: str = "utf-8"
    xml_declaration: bool = True
    pretty_print: bool = True
    parser: str = "lxml"
    stylesheet: str | Path | BytesIO | BufferedReader | None = None
    compression: str | dict[str, Any] | None = "infer"
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.index is not None:
            kwargs["index"] = self.index
        if self.root_name is not None:
            kwargs["root_name"] = self.root_name
        if self.row_name is not None:
            kwargs["row_name"] = self.row_name
        if self.na_rep is not None:
            kwargs["na_rep"] = self.na_rep
        if self.attr_cols is not None:
            kwargs["attr_cols"] = self.attr_cols
        if self.elems_cols is not None:
            kwargs["elems_cols"] = self.elems_cols
        if self.namespaces is not None:
            kwargs["namespaces"] = self.namespaces
        if self.prefix is not None:
            kwargs["prefix"] = self.prefix
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.xml_declaration is not None:
            kwargs["xml_declaration"] = self.xml_declaration
        if self.pretty_print is not None:
            kwargs["pretty_print"] = self.pretty_print
        if self.parser is not None:
            kwargs["parser"] = self.parser
        if self.stylesheet is not None:
            kwargs["stylesheet"] = self.stylesheet
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_xml(self.path_or_buffer, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path_or_buffer, data)

    @classmethod
    def name(cls) -> str:
        return "xml"


@dataclasses.dataclass
class PandasHtmlReader(DataLoader):
    """Class for loading/reading xml files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_html.html
    """

    io: str | Path | BytesIO | BufferedReader
    # kwargs
    match: str | None = ".+"
    flavor: str | Sequence | None = None
    header: int | Sequence | None = None
    index_col: int | Sequence | None = None
    skiprows: int | Sequence | slice | None = None
    attrs: dict[str, str] | None = None
    parse_dates: bool | None = None
    thousands: str | None = ","
    encoding: str | None = None
    decimal: str = "."
    converters: dict[Any, Any] | None = None
    na_values: Iterable = None
    keep_default_na: bool = True
    displayed_only: bool = True
    extract_links: Literal["header", "footer", "body", "all"] | None = None
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.match is not None:
            kwargs["match"] = self.match
        if self.flavor is not None:
            kwargs["flavor"] = self.flavor
        if self.header is not None:
            kwargs["header"] = self.header
        if self.index_col is not None:
            kwargs["index_col"] = self.index_col
        if self.skiprows is not None:
            kwargs["skiprows"] = self.skiprows
        if self.attrs is not None:
            kwargs["attrs"] = self.attrs
        if self.parse_dates is not None:
            kwargs["parse_dates"] = self.parse_dates
        if self.thousands is not None:
            kwargs["thousands"] = self.thousands
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding
        if self.decimal is not None:
            kwargs["decimal"] = self.decimal
        if self.converters is not None:
            kwargs["converters"] = self.converters
        if self.na_values is not None:
            kwargs["na_values"] = self.na_values
        if self.keep_default_na is not None:
            kwargs["keep_default_na"] = self.keep_default_na
        if self.displayed_only is not None:
            kwargs["displayed_only"] = self.displayed_only
        if self.extract_links is not None:
            kwargs["extract_links"] = self.extract_links
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options

        return kwargs

    def load_data(self, type: type) -> tuple[list[DATAFRAME_TYPE], dict[str, Any]]:
        # Loads the data and returns the df and metadata of the xml
        df = pd.read_html(self.io, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.io, df[0])
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "html"


@dataclasses.dataclass
class PandasHtmlWriter(DataSaver):
    """Class specifically to handle saving xml files/buffers with Pandas.
    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_html.html#pandas.DataFrame.to_html
    """

    buf: str | Path | StringIO | None = None
    # kwargs
    columns: list[str] | None = None
    col_space: str | int | list | dict | None = None
    header: bool | None = True
    index: bool | None = True
    na_rep: str | None = "NaN"
    formatters: list | tuple | dict | None = None
    float_format: str | None = None
    sparsify: bool | None = True
    index_names: bool | None = True
    justify: str = None
    max_rows: int | None = None
    max_cols: int | None = None
    show_dimensions: bool = False
    decimal: str = "."
    bold_rows: bool = True
    classes: str | list[str] | tuple | None = None
    escape: bool | None = True
    notebook: Literal[True, False] = False
    border: int = None
    table_id: str | None = None
    render_links: bool = False
    encoding: str | None = "utf-8"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.col_space is not None:
            kwargs["col_space"] = self.col_space
        if self.header is not None:
            kwargs["header"] = self.header
        if self.index is not None:
            kwargs["index"] = self.index
        if self.na_rep is not None:
            kwargs["na_rep"] = self.na_rep
        if self.formatters is not None:
            kwargs["formatters"] = self.formatters
        if self.float_format is not None:
            kwargs["float_format"] = self.float_format
        if self.sparsify is not None:
            kwargs["sparsify"] = self.sparsify
        if self.index_names is not None:
            kwargs["index_names"] = self.index_names
        if self.justify is not None:
            kwargs["justify"] = self.justify
        if self.max_rows is not None:
            kwargs["max_rows"] = self.max_rows
        if self.max_cols is not None:
            kwargs["max_cols"] = self.max_cols
        if self.show_dimensions is not None:
            kwargs["show_dimensions"] = self.show_dimensions
        if self.decimal is not None:
            kwargs["decimal"] = self.decimal
        if self.bold_rows is not None:
            kwargs["bold_rows"] = self.bold_rows
        if self.classes is not None:
            kwargs["classes"] = self.classes
        if self.escape is not None:
            kwargs["escape"] = self.escape
        if self.notebook is not None:
            kwargs["notebook"] = self.notebook
        if self.border is not None:
            kwargs["border"] = self.border
        if self.table_id is not None:
            kwargs["table_id"] = self.table_id
        if self.render_links is not None:
            kwargs["render_links"] = self.render_links
        if self.encoding is not None:
            kwargs["encoding"] = self.encoding

        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_html(self.buf, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.buf, data)

    @classmethod
    def name(cls) -> str:
        return "html"


@dataclasses.dataclass
class PandasStataReader(DataLoader):
    """Class for loading/reading xml files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_stata.html#pandas.read_stata
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    convert_dates: bool = True
    convert_categoricals: bool = True
    index_col: str | None = None
    convert_missing: bool = False
    preserve_dtypes: bool = True
    columns: Sequence | None = None
    order_categoricals: bool = True
    chunksize: int | None = None
    iterator: bool = False
    compression: dict[str, Any] | Literal["infer", "gzip", "bz2", "zip", "xz", "zstd", "tar"] = (
        "infer"
    )
    storage_options: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.convert_dates is not None:
            kwargs["convert_dates"] = self.convert_dates
        if self.convert_categoricals is not None:
            kwargs["convert_categoricals"] = self.convert_categoricals
        if self.index_col is not None:
            kwargs["index_col"] = self.index_col
        if self.convert_missing is not None:
            kwargs["convert_missing"] = self.convert_missing
        if self.preserve_dtypes is not None:
            kwargs["preserve_dtypes"] = self.preserve_dtypes
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.order_categoricals is not None:
            kwargs["order_categoricals"] = self.order_categoricals
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.iterator is not None:
            kwargs["iterator"] = self.iterator
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options

        return kwargs

    def load_data(self, type: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the xml
        df = pd.read_stata(self.filepath_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "stata"


@dataclasses.dataclass
class PandasStataWriter(DataSaver):
    """Class specifically to handle saving xml files/buffers with Pandas.
    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_stata.html
    """

    path: str | Path | BufferedReader = None
    # kwargs
    convert_dates: dict[Hashable, str] | None = None
    write_index: bool = True
    byteorder: str | None = None
    time_stamp: datetime | None = None
    data_label: str | None = None
    variable_labels: dict[Hashable, str] | None = None
    version: Literal[114, 117, 118, 119] = 114
    convert_strl: str | None = None
    compression: dict[str, Any] | Literal["infer", "gzip", "bz2", "zip", "xz", "zstd", "tar"] = (
        "infer"
    )
    storage_options: dict[str, Any] | None = None
    value_labels: dict[Hashable, str] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.convert_dates is not None:
            kwargs["convert_dates"] = self.convert_dates
        if self.write_index is not None:
            kwargs["write_index"] = self.write_index
        if self.byteorder is not None:
            kwargs["byteorder"] = self.byteorder
        if self.time_stamp is not None:
            kwargs["time_stamp"] = self.time_stamp
        if self.data_label is not None:
            kwargs["data_label"] = self.data_label
        if self.variable_labels is not None:
            kwargs["variable_labels"] = self.variable_labels
        if self.version is not None:
            kwargs["version"] = self.version
        if self.convert_strl is not None and self.version == 117:
            kwargs["convert_strl"] = self.convert_strl
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if self.value_labels is not None:
            kwargs["value_labels"] = self.value_labels

        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_stata(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "stata"


@dataclasses.dataclass
class PandasFeatherReader(DataLoader):
    """Class for loading/reading feather files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_feather.html
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    columns: Sequence | None = None
    use_threads: bool = True
    storage_options: dict[str, Any] | None = None
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.use_threads is not None:
            kwargs["use_threads"] = self.use_threads
        if self.storage_options is not None:
            kwargs["storage_options"] = self.storage_options
        if pd.__version__ >= "2.0" and self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend

        return kwargs

    def load_data(self, type: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the xml
        df = pd.read_feather(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "feather"


@dataclasses.dataclass
class PandasFeatherWriter(DataSaver):
    """Class specifically to handle saving xml files/buffers with Pandas.
    Should map to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_feather.html
    Additional Parameters passed to: https://arrow.apache.org/docs/python/generated/pyarrow.feather.write_feather.html#pyarrow.feather.write_feather

    Requires `lz4` https://pypi.org/project/lz4/
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    dest: str | None = None
    compression: Literal["zstd", "lz4", "uncompressed"] = None
    compression_level: int | None = None
    chunksize: int | None = None
    version: int | None = 2

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.dest is not None:
            kwargs["dest"] = self.dest
        if self.compression is not None:
            kwargs["compression"] = self.compression
        if self.compression_level is not None:
            kwargs["compression_level"] = self.compression_level
        if self.chunksize is not None:
            kwargs["chunksize"] = self.chunksize
        if self.version is not None:
            kwargs["version"] = self.version

        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_feather(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "feather"


@dataclasses.dataclass
class PandasORCReader(DataLoader):
    """
    Class that handles reading ORC files and output a pandas DataFrame
    Maps to: https://pandas.pydata.org/docs/reference/api/pandas.read_orc.html#pandas.read_orc
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    columns: list[str] | None = None
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"
    filesystem: FILESYSTEM_TYPE | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        kwargs = {}
        if self.columns is not None:
            kwargs["columns"] = self.columns
        if self.dtype_backend is not None:
            kwargs["dtype_backend"] = self.dtype_backend
        if self.filesystem is not None:
            kwargs["filesystem"] = self.filesystem

        return kwargs

    def load_data(self, type: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the orc
        df = pd.read_orc(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "orc"


@dataclasses.dataclass
class PandasORCWriter(DataSaver):
    """
    Class that handles writing DataFrames to ORC files.
    Maps to: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_orc.html
    """

    path: str | Path | BytesIO | BufferedReader
    # kwargs
    engine: Literal["pyarrow"] = "pyarrow"
    index: bool | None = None
    engine_kwargs: dict[str, Any] | None | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self):
        kwargs = {}
        if self.engine is not None:
            kwargs["engine"] = self.engine
        if self.index is not None:
            kwargs["index"] = self.index
        if self.engine_kwargs is not None:
            kwargs["engine_kwargs"] = self.engine_kwargs

        return kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        data.to_orc(self.path, **self._get_saving_kwargs())
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "orc"


@dataclasses.dataclass
class PandasExcelReader(DataLoader):
    """Class for reading Excel files and output a pandas DataFrame.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
    """

    path: str | Path | BytesIO | BufferedReader = None
    # kwargs:
    # inspect.get_type_hints doesn't work with type aliases,
    # which are used in pandas.read_excel.
    # So we have to list all the arguments in plain code.
    sheet_name: str | int | list[int | str] | None = 0
    header: int | Sequence | None = 0
    names: Sequence | None = None
    index_col: int | str | Sequence | None = None
    usecols: int | str | Sequence | Sequence | Callable[[str], bool] | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    engine: Literal["xlrd", "openpyxl", "odf", "pyxlsb", "calamine"] | None = None
    converters: dict[str, Callable] | dict[int, Callable] | None = None
    true_values: Iterable | None = None
    false_values: Iterable | None = None
    skiprows: Sequence | int | Callable[[int], object] | None = None
    nrows: int | None = None
    na_values = None  # in pandas.read_excel there are not type hints for na_values
    keep_default_na: bool = True
    na_filter: bool = True
    verbose: bool = False
    parse_dates: list[int | str] | dict[str, list[int | str]] | bool = False
    # date_parser: Optional[Callable]  # date_parser is deprecated since pandas=2.0.0
    date_format: dict[Hashable, str] | str | None = None
    thousands: str | None = None
    decimal: str = "."
    comment: str | None = None
    skipfooter: int = 0
    storage_options: dict[str, Any] | None = None
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"
    engine_kwargs: dict[str, Any] | None = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        # Returns type for which data loader is available
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = dataclasses.asdict(self)

        # path corresponds to 'io' argument of pandas.read_excel,
        # but we send it separately
        del kwargs["path"]

        # engine_kwargs appeared only in pandas >= 2.1
        # For compatibility with pandas 2.0 we remove engine_kwargs from kwargs if it's empty.
        if kwargs["engine_kwargs"] is None:
            del kwargs["engine_kwargs"]

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the excel file
        df = pd.read_excel(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "excel"


@dataclasses.dataclass
class PandasExcelWriter(DataSaver):
    """Class that handles saving Excel files with pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.ExcelWriter.html
    Additional parameters passed to https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_excel.html
    """

    path: str | Path | BytesIO
    # kwargs:
    # inspect.get_type_hints doesn't work with type aliases,
    # which are used in pandas.DataFrame.to_excel.
    # So we have to list all the arguments in plain code
    sheet_name: str = "Sheet1"
    na_rep: str = ""
    float_format: str | None = None
    columns: Sequence | None = None
    header: Sequence | bool = True
    index: bool = True
    index_label: IndexLabel | None = None
    startrow: int = 0
    startcol: int = 0
    engine: Literal["openpyxl", "xlsxwriter"] | None = None
    merge_cells: bool = True
    inf_rep: str = "inf"
    freeze_panes: tuple[int, int] | None = None
    storage_options: dict[str, Any] | None = None
    engine_kwargs: dict[str, Any] | None = None
    mode: Literal["w", "a"] | None = "w"
    if_sheet_exists: Literal["error", "new", "replace", "overlay"] | None = None
    datetime_format: str = None
    date_format: str = None

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_saving_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = dataclasses.asdict(self)

        # Pass kwargs to ExcelWriter ONLY for kwargs which appear in both ExcelWriter and .to_excel()
        writer_kwarg_names = [
            "date_format",
            "datetime_format",
            "if_sheet_exists",
            "mode",
            "engine_kwargs",
            "engine",
            "storage_options",
        ]

        # path corresponds to 'excel_writer' argument of pandas.DataFrame.to_excel,
        # but we send it separately
        del kwargs["path"]

        # engine_kwargs appeared only in pandas >= 2.1
        # For compatibility with pandas 2.0 we remove engine_kwargs from kwargs if it's empty.
        if kwargs["engine_kwargs"] is None:
            del kwargs["engine_kwargs"]
            writer_kwarg_names.remove("engine_kwargs")

        # seperate kwargs for ExcelWriter and to_excel() invocation
        writer_kwargs = {k: kwargs[k] for k in writer_kwarg_names}
        to_excel_kwargs = {k: kwargs[k] for k in (kwargs.keys() - set(writer_kwarg_names))}

        return writer_kwargs, to_excel_kwargs

    def save_data(self, data: DATAFRAME_TYPE) -> dict[str, Any]:
        writer_kwargs, to_excel_kwargs = self._get_saving_kwargs()

        with pd.ExcelWriter(self.path, **writer_kwargs) as writer:
            data.to_excel(writer, **to_excel_kwargs)
        return utils.get_file_and_dataframe_metadata(self.path, data)

    @classmethod
    def name(cls) -> str:
        return "excel"


@dataclasses.dataclass
class PandasTableReader(DataLoader):
    """Class for loading/reading table files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_table.html
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    sep: str | None = None
    delimiter: str | None = None
    header: int | Sequence | str | None = "infer"
    names: Sequence | None = None
    index_col: int | str | Sequence | None = None
    usecols: Sequence | None = None
    dtype: Dtype | dict[Hashable, Dtype] | None = None
    engine: Literal["c", "python", "pyarrow"] | None = None
    converters: dict[Hashable, Callable] | None = None
    true_values: Iterable | None = None
    false_values: Iterable | None = None
    skipinitialspace: bool = False
    skiprows: list[int] | int | list[Callable] | None = None
    skipfooter: int = 0
    nrows: int | None = None
    na_values: Hashable | Iterable | dict[Hashable, Iterable] | None = None
    keep_default_na: bool = True
    na_filter: bool = True
    verbose: bool = False
    skip_blank_lines: bool = True
    parse_dates: list[int | str] | dict[str, list[int | str]] | bool = False
    infer_datetime_format: bool = False
    keep_date_col: bool = False
    date_parser: Callable | None = None
    date_format: str | str | None = None
    dayfirst: bool = False
    cache_dates: bool = True
    iterator: bool = False
    chunksize: int | None = None
    compression: str | dict = "infer"
    thousands: str | None = None
    decimal: str = "."
    lineterminator: str | None = None
    quotechar: str | None = '"'
    quoting: int = 0
    doublequote: bool = True
    escapechar: str | None = None
    comment: str | None = None
    encoding: str | None = None
    encoding_errors: str | None = "strict"
    dialect: str | None = None
    on_bad_lines: Literal["error", "warn", "skip"] | Callable = "error"
    delim_whitespace: bool = False
    low_memory: bool = True
    memory_map: bool = False
    float_precision: Literal["high", "legacy", "round_trip"] | None = None
    storage_options: dict | None = None
    dtype_backend: Literal["numpy_nullable", "pyarrow"] = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = dataclasses.asdict(self)

        # filepath_or_buffer corresponds to 'filepath_or_buffer' argument of pandas.read_table,
        # but we send it separately
        del kwargs["filepath_or_buffer"]

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the table
        df = pd.read_table(self.filepath_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "table"


@dataclasses.dataclass
class PandasFWFReader(DataLoader):
    """Class for loading/reading fixed-width formatted files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_fwf.html
    """

    filepath_or_buffer: str | Path | BytesIO | BufferedReader
    # kwargs
    colspecs: str | list[tuple[int, int]] | tuple[int, int] = "infer"
    widths: list[int] | None = None
    infer_nrows: int = 100
    dtype_backend: Literal["numpy_nullable", "pyarrow"] = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = dataclasses.asdict(self)

        # filepath_or_buffer corresponds to 'filepath_or_buffer' argument of pandas.read_fwf,
        # but we send it separately
        del kwargs["filepath_or_buffer"]

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the fwf file
        df = pd.read_fwf(self.filepath_or_buffer, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.filepath_or_buffer, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "fwf"


@dataclasses.dataclass
class PandasSPSSReader(DataLoader):
    """Class for loading/reading spss files with Pandas.
    Maps to https://pandas.pydata.org/docs/reference/api/pandas.read_spss.html
    """

    path: str | Path
    # kwargs
    usecols: list[Hashable] | Callable[[str], bool] | None = None
    convert_categoricals: bool = True
    dtype_backend: Literal["pyarrow", "numpy_nullable"] = "numpy_nullable"

    @classmethod
    def applicable_types(cls) -> Collection[type]:
        return [DATAFRAME_TYPE]

    def _get_loading_kwargs(self) -> dict[str, Any]:
        # Puts kwargs in a dict
        kwargs = dataclasses.asdict(self)

        # path corresponds to 'io' argument of pandas.read_spss,
        # but we send it separately
        del kwargs["path"]

        return kwargs

    def load_data(self, type_: type) -> tuple[DATAFRAME_TYPE, dict[str, Any]]:
        # Loads the data and returns the df and metadata of the spss file
        df = pd.read_spss(self.path, **self._get_loading_kwargs())
        metadata = utils.get_file_and_dataframe_metadata(self.path, df)
        return df, metadata

    @classmethod
    def name(cls) -> str:
        return "spss"


def register_data_loaders():
    """Function to register the data loaders for this extension."""
    for loader in [
        PandasCSVReader,
        PandasCSVWriter,
        PandasParquetReader,
        PandasParquetWriter,
        PandasPickleReader,
        PandasPickleWriter,
        PandasJsonReader,
        PandasJsonWriter,
        PandasSqlReader,
        PandasSqlWriter,
        PandasXmlReader,
        PandasXmlWriter,
        PandasHtmlReader,
        PandasHtmlWriter,
        PandasStataReader,
        PandasStataWriter,
        PandasFeatherReader,
        PandasFeatherWriter,
        PandasORCWriter,
        PandasORCReader,
        PandasExcelWriter,
        PandasExcelReader,
        PandasTableReader,
        PandasFWFReader,
        PandasSPSSReader,
    ]:
        registry.register_adapter(loader)


register_data_loaders()
