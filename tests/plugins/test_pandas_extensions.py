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
import sys
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
    ("connect", "identified"),
    [
        (lambda _: sqlite3.connect(":memory:"), False),
        (lambda _: create_engine("sqlite://"), False),
        (lambda path: sqlite3.connect(path), True),
        (lambda path: create_engine(f"sqlite:///{path}"), True),
    ],
)
def test_pandas_sql(df: pd.DataFrame, connect, identified: bool, tmp_path) -> None:
    path = tmp_path / "test.db"
    conn = connect(path)
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
    assert metadata1["dataframe_metadata"]["datatypes"] == [str(df["foo"].dtype)]
    assert metadata1["sql_metadata"]["operation"] == "write"
    assert metadata2["sql_metadata"]["operation"] == "read"
    assert metadata1["sql_metadata"]["table_name"] == "bar"
    assert metadata2["sql_metadata"]["query"] == "SELECT foo FROM bar"
    if identified:
        expected = {"dialect": "sqlite", "database": str(path.resolve())}
        assert expected.items() <= metadata1["sql_metadata"]["source"].items()
        assert metadata1["sql_metadata"]["source"] == metadata2["sql_metadata"]["source"]
    else:
        assert metadata1["sql_metadata"]["source"] is None
        assert metadata2["sql_metadata"]["source"] is None
        assert metadata1["sql_metadata"]["notes"]

    if hasattr(conn, "close"):
        conn.close()


def test_pandas_sql_decorators_capture_source(tmp_path) -> None:
    """@load_from.sql / @save_to.sql carry datasource context with no custom metadata code."""
    from hamilton import ad_hoc_utils, driver
    from hamilton.function_modifiers import load_from, save_to, source, value

    sales = sqlite3.connect(tmp_path / "sales.db")
    pd.DataFrame({"id": [1, 2], "amount": [10.0, 5.0]}).to_sql("orders", sales, index=False)
    warehouse = create_engine(f"sqlite:///{tmp_path / 'warehouse.db'}")

    @load_from.sql(
        query_or_table=value("select id, amount from orders"), db_connection=source("sales")
    )
    def orders(df: pd.DataFrame) -> pd.DataFrame:
        return df

    @save_to.sql(
        table_name=value("revenue"),
        db_connection=source("warehouse"),
        if_exists=value("replace"),
        index=value(False),
        output_name_="saved",
    )
    def revenue(orders: pd.DataFrame) -> pd.DataFrame:
        return orders.assign(revenue=orders["amount"] * 2)

    module = ad_hoc_utils.create_temporary_module(orders, revenue)
    dr = driver.Builder().with_modules(module).build()
    result = dr.execute(
        ["orders.load_data.df", "saved"], inputs={"sales": sales, "warehouse": warehouse}
    )

    loaded_df, loaded_metadata = result["orders.load_data.df"]
    assert loaded_metadata["sql_metadata"]["source"]["database"] == str(
        (tmp_path / "sales.db").resolve()
    )
    assert loaded_metadata["sql_metadata"]["operation"] == "read"
    saved_metadata = result["saved"]
    assert saved_metadata["sql_metadata"]["source"]["database"] == str(
        (tmp_path / "warehouse.db").resolve()
    )
    assert saved_metadata["sql_metadata"]["table_name"] == "revenue"
    assert pd.read_sql("select * from revenue", warehouse)["revenue"].tolist() == [20.0, 10.0]
    sales.close()


def test_pandas_sql_postgres_forms(postgres_schema) -> None:
    """URL string, Engine and Connection forms all identify server, database and schema."""
    engine, schema = postgres_schema
    url = engine.url.render_as_string(hide_password=False)
    df = pd.DataFrame({"foo": ["bar"]})
    written = PandasSqlWriter(
        table_name="orders", db_connection=engine, schema=schema, index=False
    ).save_data(df)
    source = written["sql_metadata"]["source"]
    assert source["dialect"] == "postgresql"
    assert source["host"] == engine.url.host
    assert source["port"] == engine.url.port
    assert source["database"] == engine.url.database
    assert source["default_schema"]  # verified by SQLAlchemy at connect time, not assumed
    assert written["sql_metadata"]["schema"] == schema

    query = f"SELECT * FROM {schema}.orders"
    with engine.connect() as conn:
        df_conn, via_conn = PandasSqlReader(query_or_table=query, db_connection=conn).load_data(
            pd.DataFrame
        )
    df_url, via_url = PandasSqlReader(query_or_table=query, db_connection=url).load_data(
        pd.DataFrame
    )
    assert df.equals(df_conn) and df.equals(df_url)
    assert via_conn["sql_metadata"]["source"] == source
    assert via_url["sql_metadata"]["source"] == {**source, "default_schema": None}
    assert engine.url.password not in str(via_url)


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


def test_pandas_table_reader_translates_delim_whitespace_for_pandas_3(tmp_path) -> None:
    path = tmp_path / "table.txt"
    path.write_text("name value\nfoo 1\n")

    reader = PandasTableReader(filepath_or_buffer=path, delim_whitespace=True)
    df, _ = reader.load_data(pd.DataFrame)

    assert df.to_dict(orient="records") == [{"name": "foo", "value": 1}]


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("verbose", True),
        ("infer_datetime_format", True),
        ("infer_datetime_format", False),
        ("delim_whitespace", False),
    ],
)
def test_pandas_table_reader_rejects_removed_parameter_on_pandas_3(parameter, value) -> None:
    reader = PandasTableReader(filepath_or_buffer="unused", **{parameter: value})

    if int(pd.__version__.split(".", maxsplit=1)[0]) >= 3:
        with pytest.raises(ValueError, match=f"pandas 3.0 removed.*{parameter}"):
            reader._get_loading_kwargs()
    else:
        assert reader._get_loading_kwargs()[parameter] is value


@pytest.mark.skipif(sys.version_info >= (3, 14), reason="pyreadstat not available on Python 3.14")
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
