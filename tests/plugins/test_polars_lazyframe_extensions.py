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
import pathlib
import sys
import warnings

import polars as pl
import pytest
from packaging import version
from polars.testing import assert_frame_equal
from sqlalchemy import create_engine

from hamilton import ad_hoc_utils, driver, registry
from hamilton.io.materialization import from_
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
    PolarsNDJSONReader,
    PolarsNDJSONWriter,
    PolarsParquetWriter,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)

polars_1 = version.Version(pl.__version__) < version.Version("2.0.0")


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


def test_lazy_polars_csv_reader_options(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"
    file.write_text("a,b\n1,\n2,y\n")

    reader = PolarsScanCSVReader(
        file=file,
        dtypes={"a": pl.Float64},
        missing_utf8_is_empty_string=True,
        row_count_name="idx",
        row_count_offset=1,
    )
    df, _ = reader.load_data(pl.LazyFrame)
    df = df.collect()

    assert df.columns == ["idx", "a", "b"]
    assert df["idx"].to_list() == [1, 2]
    assert df.schema["a"] == pl.Float64
    assert df["b"].to_list() == ["", "y"]


@pytest.mark.parametrize(
    ("writer_class", "reader_class", "path_field"),
    [
        (PolarsParquetWriter, PolarsScanParquetReader, "file"),
        (PolarsFeatherWriter, PolarsScanFeatherReader, "source"),
    ],
)
def test_lazy_polars_reader_row_count_options(
    df: pl.LazyFrame, tmp_path: pathlib.Path, writer_class, reader_class, path_field
) -> None:
    file = tmp_path / "test_data"
    writer_class(file=file).save_data(df)

    reader = reader_class(**{path_field: file}, row_count_name="idx", row_count_offset=1)
    df2, _ = reader.load_data(pl.LazyFrame)

    assert df2.collect().columns == ["idx", "a", "b"]
    assert df2.collect()["idx"].to_list() == [1, 2]


@pytest.mark.xfail(
    polars_1,
    raises=TypeError,
    strict=True,
    reason="the polars 1.x CSV reader passes comment_char, which polars 1.x rejects",
)
def test_lazy_polars_csv_reader_comment_char(tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"
    file.write_text("a\n# comment\n1\n")

    df, _ = PolarsScanCSVReader(file=file, comment_char="#").load_data(pl.LazyFrame)

    assert df.collect()["a"].to_list() == [1]


polars_1_scan_readers_pass_columns = pytest.mark.xfail(
    polars_1,
    raises=TypeError,
    strict=True,
    reason="the polars 1.x scan readers pass columns, which scan_* rejects",
)

# polars 1.x still accepts these old argument names through deprecation wrappers, which
# inspect.signature does not show.
POLARS_1_RENAMED_ARGUMENTS = (
    {"dtypes", "missing_utf8_is_empty_string", "row_count_name", "row_count_offset"}
    if polars_1
    else set()
)


@pytest.mark.xfail(
    polars_1,
    strict=True,
    reason="the polars 1.x scan readers pass columns, and CSV n_threads, which scan_* rejects",
)
@pytest.mark.parametrize(
    ("name", "polars_function"),
    [("csv", pl.scan_csv), ("parquet", pl.scan_parquet), ("feather", pl.scan_ipc)],
)
def test_lazy_polars_reader_kwargs_are_accepted_by_polars(name: str, polars_function) -> None:
    readers = [
        loader
        for loader in registry.LOADER_REGISTRY[name]
        if pl.LazyFrame in loader.applicable_types()
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


@polars_1_scan_readers_pass_columns
@pytest.mark.parametrize(
    ("writer_class", "reader_class", "path_field", "polars_function", "suffix"),
    [
        (PolarsCSVWriter, PolarsScanCSVReader, "file", pl.read_csv, "csv"),
        (PolarsParquetWriter, PolarsScanParquetReader, "file", pl.read_parquet, "parquet"),
        (PolarsFeatherWriter, PolarsScanFeatherReader, "source", pl.read_ipc, "feather"),
    ],
)
@pytest.mark.parametrize("columns", [["bc"], [1], [-1], [-2], "bc"])
@pytest.mark.parametrize("row_count_name", [None, "idx"])
def test_lazy_polars_reader_columns(
    tmp_path: pathlib.Path,
    writer_class,
    reader_class,
    path_field: str,
    polars_function,
    suffix: str,
    columns: list | str,
    row_count_name: str | None,
) -> None:
    file = tmp_path / f"test.{suffix}"
    # "bc" has more than one character, so a bare string can't pass by being split into letters.
    writer_class(file=file).save_data(pl.DataFrame({"a": [1, 2], "bc": [3, 4]}))

    reader = reader_class(**{path_field: file}, columns=columns, row_count_name=row_count_name)
    loaded, _ = reader.load_data(pl.LazyFrame)

    expected = polars_function(file, columns=columns, row_index_name=row_count_name)
    assert_frame_equal(loaded.collect(), expected)


@pytest.mark.skipif(polars_1, reason="polars 1.x accepts these fields")
@pytest.mark.parametrize(
    ("reader_class", "path_field", "field"),
    [
        (PolarsScanCSVReader, "file", "n_threads"),
        (PolarsScanCSVReader, "file", "batch_size"),
        (PolarsScanCSVReader, "file", "rechunk"),
        (PolarsScanParquetReader, "file", "rechunk"),
        (PolarsScanFeatherReader, "source", "memory_map"),
        (PolarsScanFeatherReader, "source", "rechunk"),
    ],
)
def test_lazy_polars_reader_warns_on_fields_polars_2_ignores(
    reader_class, path_field: str, field: str
) -> None:
    with pytest.warns(
        UserWarning, match=f"{reader_class.__name__}.{field} has no effect"
    ) as record:
        reader_class(**{path_field: "unused", field: True})

    assert len(record) == 1
    assert record[0].filename == __file__


@pytest.mark.parametrize(
    ("reader_class", "path_field"),
    [
        (PolarsScanCSVReader, "file"),
        (PolarsScanParquetReader, "file"),
        (PolarsScanFeatherReader, "source"),
    ],
)
def test_lazy_polars_reader_defaults_do_not_warn(reader_class, path_field: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        reader_class(**{path_field: "unused"})


@pytest.mark.parametrize(
    ("name", "writer", "path_field"),
    [
        ("csv", PolarsCSVWriter, "file"),
        ("parquet", PolarsParquetWriter, "file"),
        ("feather", PolarsFeatherWriter, "source"),
    ],
)
def test_lazy_polars_readers_materialize(
    name: str, writer, path_field: str, df: pl.LazyFrame, tmp_path: pathlib.Path
) -> None:
    file = tmp_path / f"test.{name}"
    writer(file=file).save_data(df)

    def height(raw: pl.LazyFrame) -> int:
        return raw.collect().height

    dr = driver.Builder().with_modules(ad_hoc_utils.create_temporary_module(height)).build()
    _, result = dr.materialize(
        getattr(from_, name)(target="raw", **{path_field: str(file)}), additional_vars=["height"]
    )
    assert result["height"] == 2


@polars_1_scan_readers_pass_columns
@pytest.mark.parametrize(
    ("name", "writer", "path_field"),
    [
        ("csv", PolarsCSVWriter, "file"),
        ("parquet", PolarsParquetWriter, "file"),
        ("feather", PolarsFeatherWriter, "source"),
    ],
)
def test_lazy_polars_readers_materialize_columns(
    name: str, writer, path_field: str, df: pl.LazyFrame, tmp_path: pathlib.Path
) -> None:
    file = tmp_path / f"test.{name}"
    writer(file=file).save_data(df)

    def column_names(raw: pl.LazyFrame) -> list[str]:
        return raw.collect().columns

    dr = driver.Builder().with_modules(ad_hoc_utils.create_temporary_module(column_names)).build()
    _, result = dr.materialize(
        getattr(from_, name)(target="raw", columns=["b"], **{path_field: str(file)}),
        additional_vars=["column_names"],
    )
    assert result["column_names"] == ["b"]


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


def test_polars_ndjson(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
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
