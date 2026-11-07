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
import inspect
import io
import pathlib
import sqlite3
import sys
import typing
import warnings

import polars.testing
from packaging import version
from sqlalchemy import create_engine

from hamilton import ad_hoc_utils, driver, registry
from hamilton.function_modifiers import load_from, save_to, source, value
from hamilton.io import utils
from hamilton.io.materialization import from_, to

import polars as pl  # isort: skip
import pytest  # isort: skip

from hamilton.plugins import polars_extensions  # noqa: F401  # isort: skip -- registers the readers
from hamilton.plugins.polars_post_1_0_0_extensions import (  # isort: skip
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

polars_1 = version.Version(pl.__version__) < version.Version("2.0.0")
if polars_1:
    from hamilton.plugins.polars_post_1_0_0_extensions import (
        PolarsCSVReader,
        PolarsFeatherReader,
        PolarsParquetReader,
    )
else:
    from hamilton.plugins.polars_post_2_0_0_extensions import (
        PolarsCSVReader,
        PolarsFeatherReader,
        PolarsParquetReader,
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


def test_polars_csv_reader_options(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"
    file.write_text("a,b\n1,\n2,y\n")

    reader = PolarsCSVReader(
        file=file,
        dtypes={"a": pl.Float64},
        missing_utf8_is_empty_string=True,
        row_count_name="idx",
        row_count_offset=1,
    )
    df, _ = reader.load_data(pl.DataFrame)

    assert df.columns == ["idx", "a", "b"]
    assert df["idx"].to_list() == [1, 2]
    assert df.schema["a"] == pl.Float64
    assert df["b"].to_list() == ["", "y"]


@pytest.mark.parametrize(
    ("writer_class", "reader_class", "path_field"),
    [
        (PolarsParquetWriter, PolarsParquetReader, "file"),
        (PolarsFeatherWriter, PolarsFeatherReader, "source"),
    ],
)
def test_polars_reader_row_count_options(
    df: pl.DataFrame, tmp_path: pathlib.Path, writer_class, reader_class, path_field
) -> None:
    file = tmp_path / "test_data"
    writer_class(file=file).save_data(df)

    reader = reader_class(**{path_field: file}, row_count_name="idx", row_count_offset=1)
    df2, _ = reader.load_data(pl.DataFrame)

    assert df2.columns == ["idx", "a", "b"]
    assert df2["idx"].to_list() == [1, 2]


@pytest.mark.xfail(
    polars_1,
    raises=TypeError,
    strict=True,
    reason="the polars 1.x CSV reader passes comment_char, which polars 1.x rejects",
)
def test_polars_csv_reader_comment_char(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"
    file.write_text("a\n# comment\n1\n")

    df, _ = PolarsCSVReader(file=file, comment_char="#").load_data(pl.DataFrame)

    assert df["a"].to_list() == [1]


# polars 1.x still accepts these old argument names through deprecation wrappers, which
# inspect.signature does not show.
POLARS_1_RENAMED_ARGUMENTS = (
    {"dtypes", "missing_utf8_is_empty_string", "row_count_name", "row_count_offset"}
    if polars_1
    else set()
)


@pytest.mark.parametrize(
    ("name", "polars_function"),
    [
        pytest.param(
            "csv",
            pl.read_csv,
            marks=pytest.mark.xfail(
                polars_1,
                strict=True,
                reason="the polars 1.x CSV reader passes comment_char, which polars 1.x rejects",
            ),
        ),
        ("parquet", pl.read_parquet),
        ("feather", pl.read_ipc),
    ],
)
def test_polars_reader_kwargs_are_accepted_by_polars(name: str, polars_function) -> None:
    readers = [
        loader
        for loader in registry.LOADER_REGISTRY[name]
        if pl.DataFrame in loader.applicable_types()
    ]
    accepted = set(inspect.signature(polars_function).parameters) | POLARS_1_RENAMED_ARGUMENTS

    assert readers
    for reader in readers:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            every_field_set = reader(
                **{field.name: object() for field in dataclasses.fields(reader)}
            )
        assert set(every_field_set._get_loading_kwargs()) <= accepted, reader


@pytest.mark.skipif(polars_1, reason="polars 1.x accepts these fields")
@pytest.mark.parametrize(
    ("reader_class", "path_field", "field"),
    [
        (PolarsCSVReader, "file", "n_threads"),
        (PolarsCSVReader, "file", "batch_size"),
        (PolarsFeatherReader, "source", "memory_map"),
    ],
)
def test_polars_reader_warns_on_fields_polars_2_ignores(
    reader_class, path_field: str, field: str
) -> None:
    with pytest.warns(
        UserWarning, match=f"{reader_class.__name__}.{field} has no effect"
    ) as record:
        reader_class(**{path_field: "unused", field: 2})

    assert len(record) == 1
    assert record[0].filename == __file__


@pytest.mark.parametrize(
    ("reader_class", "path_field"),
    [(PolarsCSVReader, "file"), (PolarsParquetReader, "file"), (PolarsFeatherReader, "source")],
)
def test_polars_reader_defaults_do_not_warn(reader_class, path_field: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        reader_class(**{path_field: "unused"})


@pytest.mark.parametrize(
    ("writer_class", "reader_class", "path_field", "suffix"),
    [
        (PolarsCSVWriter, PolarsCSVReader, "file", "csv"),
        (PolarsParquetWriter, PolarsParquetReader, "file", "parquet"),
        (PolarsFeatherWriter, PolarsFeatherReader, "source", "feather"),
    ],
)
# A two-file glob loads as two chunks unless rechunked, so rechunk=False also pins that polars
# behaviour, which the case relies on.
@pytest.mark.parametrize(("rechunk", "n_chunks"), [(True, 1), (False, 2)])
def test_polars_reader_rechunk(
    df: pl.DataFrame,
    tmp_path: pathlib.Path,
    writer_class,
    reader_class,
    path_field: str,
    suffix: str,
    rechunk: bool,
    n_chunks: int,
) -> None:
    for part in range(2):
        writer_class(file=tmp_path / f"part{part}.{suffix}").save_data(df)

    reader = reader_class(**{path_field: str(tmp_path / f"part*.{suffix}")}, rechunk=rechunk)
    loaded, _ = reader.load_data(pl.DataFrame)

    assert loaded.height == 2 * df.height
    assert loaded.n_chunks() == n_chunks


@pytest.mark.parametrize(
    ("name", "writer", "path_field"),
    [
        ("csv", PolarsCSVWriter, "file"),
        ("parquet", PolarsParquetWriter, "file"),
        ("feather", PolarsFeatherWriter, "source"),
    ],
)
def test_polars_readers_materialize(
    name: str, writer, path_field: str, df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    file = tmp_path / f"test.{name}"
    writer(file=file).save_data(df)

    def height(raw: pl.DataFrame) -> int:
        return raw.height

    dr = driver.Builder().with_modules(ad_hoc_utils.create_temporary_module(height)).build()
    _, result = dr.materialize(
        getattr(from_, name)(target="raw", **{path_field: str(file)}), additional_vars=["height"]
    )
    assert result["height"] == 2


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


@pytest.mark.parametrize("reader", [PolarsJSONReader, PolarsNDJSONReader])
def test_getting_type_hints_json_readers(reader) -> None:
    """Tests that types can be resolved at run time, which loaders and materializers rely on."""
    typing.get_type_hints(reader)
    assert set(reader.get_required_arguments()) == {"source"}
    assert set(reader.get_optional_arguments()) == {"schema", "schema_overrides"}


@pytest.mark.parametrize(
    ("name", "writer"), [("json", PolarsJSONWriter), ("ndjson", PolarsNDJSONWriter)]
)
def test_polars_json_readers_materialize(
    name: str, writer, df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    file = tmp_path / f"test.{name}"
    writer(file=file).save_data(df)

    def height(raw: pl.DataFrame) -> int:
        return raw.height

    dr = driver.Builder().with_modules(ad_hoc_utils.create_temporary_module(height)).build()
    _, result = dr.materialize(
        getattr(from_, name)(target="raw", source=str(file)), additional_vars=["height"]
    )
    assert result["height"] == 2


def test_polars_ndjson_load_from(df: pl.DataFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.ndjson"
    PolarsNDJSONWriter(file=file).save_data(df)

    @load_from.ndjson(source=source("path"), schema_overrides=value({"a": pl.Float64}))
    def raw(df: pl.DataFrame) -> pl.DataFrame:
        return df

    dr = driver.Builder().with_modules(ad_hoc_utils.create_temporary_module(raw)).build()
    result = dr.execute(["raw"], inputs={"path": str(file)})
    assert result["raw"].schema == pl.Schema({"a": pl.Float64, "b": pl.Int64})


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


def test_polars_database_writer_does_not_identify_a_connection_string_written_through_adbc(
    df: pl.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ADBC strips ``sqlite:/{0,3}`` from the URL, so ``sqlite://sub/x.db`` writes ``sub/x.db``
    while SQLAlchemy reads it as file ``x.db`` on host ``sub``: the identity would be a guess."""
    monkeypatch.setattr(pl.DataFrame, "write_database", lambda self, *args, **kwargs: 2)
    metadata = PolarsDatabaseWriter(
        table_name="orders", connection="sqlite://sub/x.db", engine="adbc"
    ).save_data(df)

    assert metadata["sql_metadata"]["source"] is None
    assert "ADBC" in metadata["sql_metadata"]["notes"]
    assert metadata["sql_metadata"]["table_name"] == "orders"
    assert metadata["sql_metadata"]["rows"] == 2


def test_polars_database_reader_does_not_identify_an_odbc_connection_string(
    df: pl.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Polars reads a connection string only as ODBC, through arrow-odbc."""
    monkeypatch.setattr(pl, "read_database", lambda **kwargs: df)
    _, metadata = PolarsDatabaseReader(
        query="SELECT * FROM orders", connection="Driver={SQLite3};Database=shop.db"
    ).load_data(pl.DataFrame)

    assert metadata["sql_metadata"]["source"] is None
    assert "ODBC" in metadata["sql_metadata"]["notes"]
    assert metadata["sql_metadata"]["rows"] == 2


@pytest.mark.parametrize("engine", ["sqlalchemy", "auto"])
def test_polars_database_writer_identifies_a_connection_string_written_through_sqlalchemy(
    df: pl.DataFrame, tmp_path: pathlib.Path, engine: str
) -> None:
    """Polars hands the string to ``create_engine``, so it names the database SQLAlchemy opens."""
    url = f"sqlite:///{tmp_path}/shop.db"
    metadata = PolarsDatabaseWriter(
        table_name="orders", connection=url, engine=engine, if_table_exists="replace"
    ).save_data(df)

    expected_source, _ = utils.get_sql_source(create_engine(url))
    assert expected_source is not None
    assert metadata["sql_metadata"]["source"] == expected_source


def test_polars_database_writer_auto_engine_lets_polars_choose(
    df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    """Polars selects the engine when none is given; it rejects ``engine="auto"`` itself."""
    writer = PolarsDatabaseWriter(
        table_name="orders", connection=f"sqlite:///{tmp_path}/auto.db", engine="auto"
    )

    assert "engine" not in writer._get_saving_kwargs()
    assert writer.save_data(df)["sql_metadata"]["rows"] == 2


@pytest.mark.parametrize("reported", [-1, None, "unknown"])
def test_polars_database_records_an_unreported_row_count_as_unknown(
    df: pl.DataFrame, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, reported
) -> None:
    """Drivers that report no row count make ``write_database`` return -1 (DBAPI's rowcount)."""
    monkeypatch.setattr(pl.DataFrame, "write_database", lambda self, *args, **kwargs: reported)
    metadata = PolarsDatabaseWriter(
        table_name="orders", connection=create_engine(f"sqlite:///{tmp_path}/rows.db")
    ).save_data(df)

    assert metadata["sql_metadata"]["rows"] is None
    assert metadata["sql_metadata"]["table_name"] == "orders"


def test_polars_database_records_a_reported_zero_row_count(
    df: pl.DataFrame, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pl.DataFrame, "write_database", lambda self, *args, **kwargs: 0)
    metadata = PolarsDatabaseWriter(
        table_name="orders", connection=create_engine(f"sqlite:///{tmp_path}/rows.db")
    ).save_data(df)

    assert metadata["sql_metadata"]["rows"] == 0


def test_polars_database_reader_identifies_a_sqlite3_connection(
    df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    db_path = tmp_path / "shop.db"
    PolarsDatabaseWriter(
        table_name="orders", connection=f"sqlite:///{db_path}", if_table_exists="replace"
    ).save_data(df)

    _, metadata = PolarsDatabaseReader(
        query="SELECT * FROM orders", connection=sqlite3.connect(db_path)
    ).load_data(pl.DataFrame)

    assert metadata["sql_metadata"]["source"]["dialect"] == "sqlite"
    assert metadata["sql_metadata"]["source"]["database"] == db_path.resolve().as_posix()


def test_polars_database_batched_read_records_no_row_count(
    df: pl.DataFrame, tmp_path: pathlib.Path
) -> None:
    """Covers the metadata only. The OpenLineage adapter does not yet emit a dataset for a batched
    read: its schema facet cannot take the column names of a generator."""
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
        (".orders", "orders", None),
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


@pytest.mark.parametrize("reported", [-1, None, "unknown"])
def test_pre_1_0_polars_database_records_an_unreported_row_count_as_unknown(
    df: pl.DataFrame, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, reported
) -> None:
    from hamilton.plugins import polars_pre_1_0_0_extension as pre_1_0

    monkeypatch.setattr(pl.DataFrame, "write_database", lambda self, *args, **kwargs: reported)
    metadata = pre_1_0.PolarsDatabaseWriter(
        table_name="orders", connection=f"sqlite:///{tmp_path}/pre.db"
    ).save_data(df)

    assert metadata["sql_metadata"]["rows"] is None


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


def connection_of_kind(kind: str, db_path: pathlib.Path):
    """A connection Polars accepts, in one of the forms the database classes are typed for."""
    if kind == "engine":
        return create_engine(f"sqlite:///{db_path}")
    if kind == "sqlite3":
        return sqlite3.connect(db_path)
    return f"sqlite:///{db_path}"


def connection_node(name: str, connection) -> typing.Callable:
    """A node that hands ``connection`` downstream, typed as the connection's own class."""

    def node_fn():
        return connection

    node_fn.__name__ = node_fn.__qualname__ = name
    node_fn.__annotations__ = {"return": type(connection)}
    return node_fn


# Polars writes through a SQLAlchemy Engine or URL string and reads through an Engine or a DBAPI
# connection; it rejects a sqlite3 connection for writes and a URL string for reads itself.
DATABASE_CONNECTION_KINDS = [("engine", "engine"), ("url", "sqlite3")]


def connection_inputs(way, write_kind, read_kind, db_path):
    """Hands the connections to the graph as driver inputs or as upstream nodes."""
    connections = {
        "write_connection": connection_of_kind(write_kind, db_path),
        "read_connection": connection_of_kind(read_kind, db_path),
    }
    if way == "input":
        return [], connections
    return [connection_node(name, conn) for name, conn in connections.items()], {}


@pytest.mark.parametrize("way", ["input", "upstream node"])
@pytest.mark.parametrize(("write_kind", "read_kind"), DATABASE_CONNECTION_KINDS)
def test_polars_database_decorators_resolve_connection_types(
    df: pl.DataFrame, tmp_path: pathlib.Path, way: str, write_kind: str, read_kind: str
) -> None:
    """``@save_to.database`` and ``@load_from.database`` build and run with nothing patched in.

    Hamilton reads the classes' type hints to type the ``connection`` dependency, so the
    annotation has to resolve at runtime and accept every connection Polars accepts.
    """

    @save_to.database(
        table_name=value("orders"),
        connection=source("write_connection"),
        if_table_exists=value("replace"),
        output_name_="saved_orders",
    )
    def orders_to_save(raw_orders: pl.DataFrame) -> pl.DataFrame:
        return raw_orders

    @load_from.database(query=value("SELECT * FROM orders"), connection=source("read_connection"))
    def orders_read(orders_df: pl.DataFrame) -> pl.DataFrame:
        return orders_df

    nodes, inputs = connection_inputs(way, write_kind, read_kind, tmp_path / "shop.db")
    module = ad_hoc_utils.create_temporary_module(orders_to_save, orders_read, *nodes)
    dr = driver.Builder().with_modules(module).build()

    saved = dr.execute(["saved_orders"], inputs={**inputs, "raw_orders": df})["saved_orders"]
    read = dr.execute(["orders_read"], inputs=inputs)["orders_read"]

    assert saved["sql_metadata"]["rows"] == 2
    polars.testing.assert_frame_equal(read, df)


@pytest.mark.parametrize("way", ["input", "upstream node"])
@pytest.mark.parametrize(("write_kind", "read_kind"), DATABASE_CONNECTION_KINDS)
def test_polars_database_materializers_resolve_connection_types(
    df: pl.DataFrame, tmp_path: pathlib.Path, way: str, write_kind: str, read_kind: str
) -> None:
    """``to.database`` and ``from_.database`` build and run with nothing patched in."""

    def raw_orders() -> pl.DataFrame:
        return df

    def orders_read(orders_df: pl.DataFrame) -> pl.DataFrame:
        return orders_df

    nodes, inputs = connection_inputs(way, write_kind, read_kind, tmp_path / "shop.db")
    module = ad_hoc_utils.create_temporary_module(raw_orders, orders_read, *nodes)
    dr = driver.Builder().with_modules(module).build()

    saved, _ = dr.materialize(
        to.database(
            id="saved_orders",
            dependencies=["raw_orders"],
            table_name="orders",
            connection=source("write_connection"),
            if_table_exists="replace",
        ),
        inputs=inputs,
    )
    _, result = dr.materialize(
        from_.database(
            target="orders_df",
            query="SELECT * FROM orders",
            connection=source("read_connection"),
        ),
        additional_vars=["orders_read"],
        inputs=inputs,
    )

    assert saved["saved_orders"]["sql_metadata"]["rows"] == 2
    polars.testing.assert_frame_equal(result["orders_read"], df)
