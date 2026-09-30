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

import io
import pathlib
import sqlite3
import sys
import typing

import polars.testing
from sqlalchemy import create_engine

import polars as pl  # isort: skip
import pytest  # isort: skip

from hamilton.plugins.polars_post_1_0_0_extensions import (  # isort: skip
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsCSVReader,
    PolarsCSVWriter,
    PolarsDatabaseReader,
    PolarsDatabaseWriter,
    PolarsFeatherReader,
    PolarsFeatherWriter,
    PolarsJSONReader,
    PolarsJSONWriter,
    PolarsNDJSONReader,
    PolarsNDJSONWriter,
    PolarsParquetReader,
    PolarsParquetWriter,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)

try:
    from xlsxwriter.workbook import Workbook
except ImportError:
    Workbook = type


@pytest.fixture
def df():
    yield pl.DataFrame({"a": [1, 2], "b": [3, 4]})


def test_polars_csv(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"

    writer = PolarsCSVWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsCSVReader(file=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsCSVWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsCSVReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["separator"] == ","
    assert kwargs2["has_header"] is True
    polars.testing.assert_frame_equal(df, df2)


def test_polars_parquet(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.parquet"

    writer = PolarsParquetWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsParquetReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsParquetWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsParquetReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["compression"] == "zstd"
    assert kwargs2["n_rows"] == 2
    polars.testing.assert_frame_equal(df, df2)


def test_polars_feather(tmp_path: pathlib.Path) -> None:
    test_data_file_path = "tests/resources/data/test_load_from_data.feather"
    reader = PolarsFeatherReader(source=test_data_file_path)
    read_kwargs = reader._get_loading_kwargs()
    df, _ = reader.load_data(pl.DataFrame)

    file_path = tmp_path / "test.dta"
    writer = PolarsFeatherWriter(file=file_path)
    write_kwargs = writer._get_saving_kwargs()
    metadata = writer.save_data(df)

    assert PolarsFeatherReader.applicable_types() == [pl.DataFrame]
    assert "n_rows" not in read_kwargs
    assert df.shape == (4, 3)

    assert PolarsFeatherWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert "compression" in write_kwargs
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["animal", "points", "environment"]
    assert metadata["dataframe_metadata"]["datatypes"] == ["String", "Int64", "String"]


def test_polars_json(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.json"
    writer = PolarsJSONWriter(file=file)
    writer.save_data(df)

    reader = PolarsJSONReader(source=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsJSONWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsJSONReader.applicable_types() == [pl.DataFrame]
    assert df2.shape == (2, 2)
    assert "schema" not in kwargs2
    polars.testing.assert_frame_equal(df, df2)


def test_polars_ndjson(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.ndjson"
    writer = PolarsNDJSONWriter(file=file)
    writer.save_data(df)

    reader = PolarsNDJSONReader(source=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsNDJSONWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsNDJSONReader.applicable_types() == [pl.DataFrame]
    assert df2.shape == (2, 2)
    assert "schema" not in kwargs2
    polars.testing.assert_frame_equal(df, df2)


def test_polars_avro(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.avro"

    writer = PolarsAvroWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsAvroReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsAvroWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsAvroReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["compression"] == "uncompressed"
    assert kwargs2["n_rows"] == 2
    polars.testing.assert_frame_equal(df, df2)


@pytest.mark.skipif(
    sys.version_info.major == 3 and sys.version_info.minor == 12,
    reason="weird connectorx error on 3.12",
)
def test_polars_database(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    table_name = "test_table"

    connector = create_engine(f"sqlite:///{tmp_path}/test.db")

    writer = PolarsDatabaseWriter(
        table_name=table_name, connection=connector, if_table_exists="replace"
    )
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsDatabaseReader(query=f"SELECT * FROM {table_name}", connection=connector)
    kwargs2 = reader._get_loading_kwargs()

    df2, metadata = reader.load_data(pl.DataFrame)

    assert PolarsDatabaseWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsDatabaseReader.applicable_types() == [pl.DataFrame]
    assert kwargs1["if_table_exists"] == "replace"
    assert "batch_size" not in kwargs2
    assert df2.shape == (2, 2)
    polars.testing.assert_frame_equal(df, df2)


def test_polars_spreadsheet(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.xlsx"
    writer = PolarsSpreadsheetWriter(workbook=file_path, worksheet="test_load_from_data_sheet")
    write_kwargs = writer._get_saving_kwargs()
    metadata = writer.save_data(df)

    reader = PolarsSpreadsheetReader(source=file_path, sheet_name="test_load_from_data_sheet")
    read_kwargs = reader._get_loading_kwargs()
    df2, _ = reader.load_data(pl.DataFrame)

    assert PolarsSpreadsheetWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsSpreadsheetReader.applicable_types() == [pl.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert df.shape == (2, 2)
    assert metadata["dataframe_metadata"]["column_names"] == ["a", "b"]
    assert metadata["dataframe_metadata"]["datatypes"] == ["Int64", "Int64"]
    polars.testing.assert_frame_equal(df, df2)
    assert "include_header" in write_kwargs
    assert write_kwargs["include_header"] is True
    assert "raise_if_empty" in read_kwargs
    assert read_kwargs["raise_if_empty"] is True


def test_getting_type_hints_spreadsheetwriter():
    """Tests that types can be resolved at run time."""
    type_hints = typing.get_type_hints(PolarsSpreadsheetWriter)
    assert type_hints["workbook"] == typing.Union[Workbook, io.BytesIO, pathlib.Path, str]


def test_polars_database_records_row_counts(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    connector = create_engine(f"sqlite:///{tmp_path}/rows.db")
    writer = PolarsDatabaseWriter(
        table_name="rows_table", connection=connector, if_table_exists="replace"
    )
    write_metadata = writer.save_data(df)
    assert write_metadata["sql_metadata"]["rows"] == 2
    assert write_metadata["sql_metadata"]["table_name"] == "rows_table"
    assert write_metadata["sql_metadata"]["operation"] == "write"

    reader = PolarsDatabaseReader(query="SELECT * FROM rows_table", connection=connector)
    _, read_metadata = reader.load_data(pl.DataFrame)
    assert read_metadata["sql_metadata"]["rows"] == 2
    assert read_metadata["sql_metadata"]["operation"] == "read"
    assert read_metadata["sql_metadata"]["query"] == "SELECT * FROM rows_table"


def test_polars_database_batched_read_records_no_row_count(
    df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    connector = create_engine(f"sqlite:///{tmp_path}/batched.db")
    PolarsDatabaseWriter(
        table_name="batched", connection=connector, if_table_exists="replace"
    ).save_data(df)

    reader = PolarsDatabaseReader(
        query="SELECT * FROM batched", connection=connector, iter_batches=True, batch_size=1
    )
    batches, metadata = reader.load_data(pl.DataFrame)

    assert metadata["sql_metadata"]["rows"] is None
    assert metadata["sql_metadata"]["source"]["dialect"] == "sqlite"
    assert sum(len(batch) for batch in batches) == 2


def test_polars_database_keeps_file_metadata(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    connector = create_engine(f"sqlite:///{tmp_path}/legacy.db")
    write_metadata = PolarsDatabaseWriter(
        table_name="legacy", connection=connector, if_table_exists="replace"
    ).save_data(df)
    _, read_metadata = PolarsDatabaseReader(
        query="SELECT * FROM legacy", connection=connector
    ).load_data(pl.DataFrame)

    assert write_metadata["file_metadata"]["path"] == "legacy"
    assert read_metadata["file_metadata"]["path"] == "SELECT * FROM legacy"
    assert "dataframe_metadata" in write_metadata and "dataframe_metadata" in read_metadata


@pytest.mark.parametrize(
    ("table_name", "expected_table", "expected_schema"),
    [
        ("orders", "orders", None),
        ("main.orders", "orders", "main"),
        ('"my-tbl"', "my-tbl", None),
        ('main."my-tbl"', "my-tbl", "main"),
        ('"main".orders', "orders", "main"),
        ('"a.b"', "a.b", None),
    ],
)
def test_polars_database_writer_records_the_table_and_schema_as_polars_unpacks_them(
    df: pl.DataFrame,
    tmp_path: pathlib.Path,
    table_name: str,
    expected_table: str,
    expected_schema: str | None,
) -> None:
    connector = create_engine(f"sqlite:///{tmp_path}/qualified.db")
    metadata = PolarsDatabaseWriter(
        table_name=table_name, connection=connector, if_table_exists="replace"
    ).save_data(df)

    assert metadata["sql_metadata"]["table_name"] == expected_table
    assert metadata["sql_metadata"]["schema"] == expected_schema
    assert metadata["file_metadata"]["path"] == table_name


def test_pre_1_0_polars_database_records_row_counts(
    df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    from hamilton.plugins import polars_pre_1_0_0_extension as pre_1_0

    url = f"sqlite:///{tmp_path}/pre.db"
    write_metadata = pre_1_0.PolarsDatabaseWriter(
        table_name="pre", connection=url, if_table_exists="replace"
    ).save_data(df)
    assert write_metadata["sql_metadata"]["rows"] == 2

    connection = sqlite3.connect(tmp_path / "pre.db")
    _, read_metadata = pre_1_0.PolarsDatabaseReader(
        query="SELECT * FROM pre", connection=connection
    ).load_data(pl.DataFrame)
    assert read_metadata["sql_metadata"]["rows"] == 2

    batches, batched_metadata = pre_1_0.PolarsDatabaseReader(
        query="SELECT * FROM pre", connection=connection, iter_batches=True, batch_size=1
    ).load_data(pl.DataFrame)
    assert batched_metadata["sql_metadata"]["rows"] is None
    assert sum(len(batch) for batch in batches) == 2
