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

import pathlib
import sys

import polars as pl
import pytest
from polars.testing import assert_frame_equal
from sqlalchemy import create_engine

from hamilton.plugins.polars_lazyframe_extensions import (
    PolarsScanCSVReader,
    PolarsScanFeatherReader,
    PolarsScanParquetReader,
)
from hamilton.plugins.polars_post_1_0_0_extensions import (
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsCSVWriter,
    PolarsDatabaseReader,
    PolarsDatabaseWriter,
    PolarsFeatherWriter,
    PolarsJSONReader,
    PolarsJSONWriter,
    PolarsParquetWriter,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)


@pytest.fixture
def df():
    yield pl.LazyFrame({"a": [1, 2], "b": [3, 4]})


def test_lazy_polars_lazyframe_csv(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"

    writer = PolarsCSVWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsScanCSVReader(file=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.LazyFrame)

    assert PolarsCSVWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsScanCSVReader.applicable_types() == [pl.LazyFrame]
    assert kwargs1["separator"] == ","
    assert kwargs2["has_header"] is True
    assert_frame_equal(df.collect(), df2.collect())


def test_lazy_polars_parquet(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.parquet"

    writer = PolarsParquetWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsScanParquetReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pl.LazyFrame)

    assert PolarsParquetWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsScanParquetReader.applicable_types() == [pl.LazyFrame]
    assert kwargs1["compression"] == "zstd"
    assert kwargs2["n_rows"] == 2
    assert_frame_equal(df.collect(), df2.collect())


def test_lazy_polars_feather(tmp_path: pathlib.Path) -> None:
    test_data_file_path = "tests/resources/data/test_load_from_data.feather"
    reader = PolarsScanFeatherReader(source=test_data_file_path)
    read_kwargs = reader._get_loading_kwargs()
    df, _ = reader.load_data(pl.LazyFrame)

    file_path = tmp_path / "test.dta"
    writer = PolarsFeatherWriter(file=file_path)
    write_kwargs = writer._get_saving_kwargs()
    metadata = writer.save_data(df.collect())

    assert PolarsScanFeatherReader.applicable_types() == [pl.LazyFrame]
    assert "n_rows" not in read_kwargs
    assert df.collect().shape == (4, 3)

    assert PolarsFeatherWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert "compression" in write_kwargs
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "animal",
        "points",
        "environment",
    ]
    assert metadata["dataframe_metadata"]["datatypes"] == ["String", "Int64", "String"]


def test_lazy_polars_avro(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
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
    assert_frame_equal(df.collect(), df2)


def test_polars_json(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
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
    assert_frame_equal(df.collect(), df2)


@pytest.mark.skipif(
    sys.version_info.major == 3 and sys.version_info.minor == 12,
    reason="weird connectorx error on 3.12",
)
def test_polars_database(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    connector = create_engine(f"sqlite:///{tmp_path}/test.db")
    table_name = "test_table"

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
    assert_frame_equal(df.collect(), df2)


def test_polars_spreadsheet(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
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
    assert df.collect().shape == (2, 2)
    assert metadata["dataframe_metadata"]["column_names"] == ["a", "b"]
    assert metadata["dataframe_metadata"]["datatypes"] == ["Int64", "Int64"]
    assert_frame_equal(df.collect(), df2)
    assert "include_header" in write_kwargs
    assert write_kwargs["include_header"] is True
    assert "raise_if_empty" in read_kwargs
    assert read_kwargs["raise_if_empty"] is True
