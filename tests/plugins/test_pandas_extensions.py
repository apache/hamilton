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

import os
import pathlib
import sqlite3
from typing import Union
from unittest import mock

import pandas as pd
import pytest
import tzdata
from pandas.testing import assert_frame_equal
from sqlalchemy import create_engine

from hamilton.plugins.pandas_extensions import (
    PandasCSVReader,
    PandasCSVWriter,
    PandasExcelReader,
    PandasExcelWriter,
    PandasFeatherReader,
    PandasFeatherWriter,
    PandasFWFReader,
    PandasHtmlReader,
    PandasHtmlWriter,
    PandasJsonReader,
    PandasJsonWriter,
    PandasORCReader,
    PandasORCWriter,
    PandasParquetReader,
    PandasParquetWriter,
    PandasPickleReader,
    PandasPickleWriter,
    PandasSPSSReader,
    PandasSqlReader,
    PandasSqlWriter,
    PandasStataReader,
    PandasStataWriter,
    PandasTableReader,
    PandasXmlReader,
    PandasXmlWriter,
)


@pytest.fixture
def df():
    yield pd.DataFrame({"foo": ["bar"]})


def test_pandas_parquet(df: pd.DataFrame, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "sample_df.parquet.gzip"
    writer = PandasParquetWriter(path=file_path, engine="pyarrow")
    writer.save_data(df)

    reader = PandasParquetReader(path=file_path, engine="pyarrow")
    read_df, metadata = reader.load_data(pd.DataFrame)

    assert_frame_equal(read_df, df, check_dtype=False)
    assert read_df.shape == df.shape, "DataFrames do not match"
    assert read_df.columns == df.columns
    assert len(list(tmp_path.iterdir())) == 1, "Unexpected number of files in tmp_path directory."


def test_pandas_pickle(df: pd.DataFrame, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "sample_df.pkl"
    writer = PandasPickleWriter(path=file_path)
    writer.save_data(df)

    reader = PandasPickleReader(filepath_or_buffer=file_path)
    read_df, metadata = reader.load_data(pd.DataFrame)

    assert read_df.equals(df), "DataFrames do not match"
    assert len(list(tmp_path.iterdir())) == 1, "Unexpected number of files in tmp_path directory."


def test_pandas_json(df: pd.DataFrame, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.json"

    writer = PandasJsonWriter(filepath_or_buffer=file_path, indent=4)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PandasJsonReader(filepath_or_buffer=file_path, encoding="utf-8")
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata = reader.load_data(pd.DataFrame)

    assert PandasJsonReader.applicable_types() == [pd.DataFrame]
    assert PandasJsonWriter.applicable_types() == [pd.DataFrame]
    assert kwargs1["indent"] == 4
    assert kwargs2["encoding"] == "utf-8"
    assert df.equals(df2)


@pytest.mark.parametrize(
    "conn",
    [
        sqlite3.connect(":memory:"),
        create_engine("sqlite://"),
    ],
)
def test_pandas_sql(df: pd.DataFrame, conn: Union[str, sqlite3.Connection]) -> None:
    writer = PandasSqlWriter(table_name="bar", db_connection=conn)
    kwargs1 = writer._get_saving_kwargs()
    metadata1 = writer.save_data(df)

    reader = PandasSqlReader(query_or_table="SELECT foo FROM bar", db_connection=conn)
    kwargs2 = reader._get_loading_kwargs()
    df2, metadata2 = reader.load_data(pd.DataFrame)

    assert PandasSqlReader.applicable_types() == [pd.DataFrame]
    assert PandasSqlWriter.applicable_types() == [pd.DataFrame]
    assert kwargs1["if_exists"] == "fail"
    assert kwargs2["coerce_float"] is True
    assert df.equals(df2)

    assert metadata1["sql_metadata"]["rows"] == 1
    assert metadata2["sql_metadata"]["rows"] == 1
    assert metadata1["dataframe_metadata"]["datatypes"] == ["object"]

    if hasattr(conn, "close"):
        conn.close()


def test_pandas_xml_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.xml"
    reader = PandasXmlReader(path_or_buffer=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasXmlReader.applicable_types() == [pd.DataFrame]
    assert df.shape == (4, 4)


def test_pandas_xml_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.xml"
    writer = PandasXmlWriter(path_or_buffer=file_path)
    metadata = writer.save_data(pd.DataFrame({"foo": ["bar"]}))

    assert PandasXmlWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["foo"]
    assert "__version__" in metadata["file_metadata"]
    assert "__version__" in metadata["dataframe_metadata"]


def test_pandas_html_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.html"
    reader = PandasHtmlReader(io=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasHtmlReader.applicable_types() == [pd.DataFrame]
    assert df[0].shape == (3, 4)


def test_pandas_html_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.xml"
    writer = PandasHtmlWriter(buf=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasHtmlWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]


def test_pandas_stata_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.dta"
    reader = PandasStataReader(filepath_or_buffer=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasStataReader.applicable_types() == [pd.DataFrame]
    assert df.shape == (4, 4)


def test_pandas_stata_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.dta"
    writer = PandasStataWriter(path=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasStataWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]


def test_pandas_feather_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.feather"
    reader = PandasFeatherReader(path=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasFeatherReader.applicable_types() == [pd.DataFrame]
    assert df.shape == (4, 3)


def test_pandas_feather_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.dta"
    writer = PandasFeatherWriter(path=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasStataWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]
    assert "__version__" in metadata["file_metadata"]
    assert "__version__" in metadata["dataframe_metadata"]


def test_pandas_csv_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.csv"
    reader = PandasCSVReader(path=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasCSVReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]


def test_pandas_csv_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.csv"
    writer = PandasCSVWriter(path=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasCSVWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]


def test_pandas_orc_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.orc"
    writer = PandasORCWriter(path=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasORCWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]


@mock.patch.dict(os.environ, {"TZDIR": os.path.join(os.path.dirname(tzdata.__file__), "zoneinfo")})
def test_pandas_orc_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.orc"
    reader = PandasORCReader(path=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasORCReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]


def test_pandas_excel_writer(tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "test.xlsx"
    writer = PandasExcelWriter(path=file_path)
    metadata = writer.save_data(pd.DataFrame(data={"col1": [1, 2], "col2": [4, 3]}))

    assert PandasExcelWriter.applicable_types() == [pd.DataFrame]
    assert file_path.exists()
    assert metadata["file_metadata"]["path"] == str(file_path)
    assert metadata["dataframe_metadata"]["column_names"] == ["col1", "col2"]


def test_pandas_excel_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.xlsx"
    reader = PandasExcelReader(path=path_to_test, sheet_name="test_load_from_data_sheet")
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasExcelReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]


def test_pandas_table_reader(tmp_path: pathlib.Path) -> None:
    path_to_test = "tests/resources/data/test_load_from_data.csv"
    reader = PandasTableReader(filepath_or_buffer=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasTableReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]


def test_pandas_spss_reader(tmp_path: pathlib.Path) -> None:
    import pyreadstat

    path_to_test = "tests/resources/data/test_load_from_data.xlsx"
    reader = PandasExcelReader(path=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)
    pyreadstat.write_sav(df, tmp_path / "test.sav")

    reader = PandasSPSSReader(path=tmp_path / "test.sav")
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasSPSSReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]


def test_pandas_fwf_reader() -> None:
    path_to_test = "tests/resources/data/test_load_from_data.fwf"
    reader = PandasFWFReader(filepath_or_buffer=path_to_test)
    df, metadata = reader.load_data(pd.DataFrame)

    assert PandasFWFReader.applicable_types() == [pd.DataFrame]
    assert df.loc[0, "firstName"] == "John"
    assert df.shape == (3, 5)
    assert metadata["dataframe_metadata"]["column_names"] == [
        "firstName",
        "lastName",
        "age",
        "department",
        "email",
    ]
