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

from hamilton import ad_hoc_utils, driver, registry
from hamilton.function_modifiers.adapters import resolve_adapter_class
from hamilton.io.materialization import to
from hamilton.plugins.polars_lazyframe_extensions import (
    PolarsScanCSVReader,
    PolarsScanFeatherReader,
    PolarsScanParquetReader,
    PolarsSinkCSVWriter,
    PolarsSinkFeatherWriter,
    PolarsSinkNDJSONWriter,
    PolarsSinkParquetWriter,
)
from hamilton.plugins.polars_post_1_0_0_extensions import (
    PolarsAvroReader,
    PolarsAvroWriter,
    PolarsDatabaseReader,
    PolarsDatabaseWriter,
    PolarsFeatherWriter,
    PolarsJSONReader,
    PolarsJSONWriter,
    PolarsNDJSONReader,
    PolarsSpreadsheetReader,
    PolarsSpreadsheetWriter,
)
from hamilton.plugins.polars_pre_1_0_0_extension import (
    PolarsCSVWriter as Pre1PolarsCSVWriter,
)
from hamilton.plugins.polars_pre_1_0_0_extension import (
    PolarsFeatherWriter as Pre1PolarsFeatherWriter,
)
from hamilton.plugins.polars_pre_1_0_0_extension import (
    PolarsParquetWriter as Pre1PolarsParquetWriter,
)


@pytest.fixture
def df():
    yield pl.LazyFrame({"a": [1, 2], "b": [3, 4]})


def test_lazy_polars_lazyframe_csv(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"

    writer = PolarsSinkCSVWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsScanCSVReader(file=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, _metadata = reader.load_data(pl.LazyFrame)

    assert PolarsSinkCSVWriter.applicable_types() == [pl.LazyFrame]
    assert PolarsScanCSVReader.applicable_types() == [pl.LazyFrame]
    assert kwargs1["separator"] == ","
    assert kwargs2["has_header"] is True
    assert_frame_equal(df.collect(), df2.collect())


def test_lazy_polars_parquet(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.parquet"

    writer = PolarsSinkParquetWriter(file=file)
    kwargs1 = writer._get_saving_kwargs()
    writer.save_data(df)

    reader = PolarsScanParquetReader(file=file, n_rows=2)
    kwargs2 = reader._get_loading_kwargs()
    df2, _metadata = reader.load_data(pl.LazyFrame)

    assert PolarsSinkParquetWriter.applicable_types() == [pl.LazyFrame]
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

    assert PolarsFeatherWriter.applicable_types() == [pl.DataFrame]
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
    df2, _metadata = reader.load_data(pl.DataFrame)

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
    df2, _metadata = reader.load_data(pl.DataFrame)

    assert PolarsJSONWriter.applicable_types() == [pl.DataFrame, pl.LazyFrame]
    assert PolarsJSONReader.applicable_types() == [pl.DataFrame]
    assert df2.shape == (2, 2)
    assert "schema" not in kwargs2
    assert_frame_equal(df.collect(), df2)


def test_polars_ndjson(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.ndjson"
    writer = PolarsSinkNDJSONWriter(file=file)
    writer.save_data(df)

    reader = PolarsNDJSONReader(source=file)
    kwargs2 = reader._get_loading_kwargs()
    df2, _metadata = reader.load_data(pl.DataFrame)

    assert PolarsSinkNDJSONWriter.applicable_types() == [pl.LazyFrame]
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
    df2, _metadata = reader.load_data(pl.DataFrame)

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


def test_polars_lazyframe_sink_parquet(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.parquet"
    sink = PolarsSinkParquetWriter(file=file)
    kwargs = sink._get_saving_kwargs()
    metadata = sink.save_data(df)
    df2 = pl.read_parquet(file)

    assert PolarsSinkParquetWriter.applicable_types() == [pl.LazyFrame]
    assert file.exists()
    assert kwargs["compression"] == "zstd"
    assert metadata["file_metadata"]["path"] == str(file)
    assert_frame_equal(df.collect(), df2)


def test_polars_lazyframe_sink_parquet_custom_kwargs(
    df: pl.LazyFrame, tmp_path: pathlib.Path
) -> None:
    """Test that non-default kwargs are passed through correctly."""
    file = tmp_path / "test.parquet"
    sink = PolarsSinkParquetWriter(file=file, compression="snappy", maintain_order=False)
    kwargs = sink._get_saving_kwargs()
    sink.save_data(df)
    df2 = pl.read_parquet(file)

    assert kwargs["compression"] == "snappy"
    assert kwargs["maintain_order"] is False
    assert file.exists()
    assert_frame_equal(df.collect().sort(["a", "b"]), df2.sort(["a", "b"]))


def test_polars_lazyframe_sink_csv(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.csv"
    sink = PolarsSinkCSVWriter(file=file)
    kwargs = sink._get_saving_kwargs()
    metadata = sink.save_data(df)
    df2 = pl.read_csv(file)

    assert PolarsSinkCSVWriter.applicable_types() == [pl.LazyFrame]
    assert file.exists()
    assert kwargs["separator"] == ","
    assert kwargs["include_header"] is True
    assert metadata["file_metadata"]["path"] == str(file)
    assert_frame_equal(df.collect(), df2)


def test_polars_lazyframe_sink_csv_custom_kwargs(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    """Test that non-default kwargs are passed through correctly."""
    file = tmp_path / "test.csv"
    sink = PolarsSinkCSVWriter(file=file, separator=";", include_header=False)
    kwargs = sink._get_saving_kwargs()
    sink.save_data(df)
    df2 = pl.read_csv(file, separator=";", has_header=False, new_columns=["a", "b"])

    assert kwargs["separator"] == ";"
    assert kwargs["include_header"] is False
    assert file.exists()
    assert_frame_equal(df.collect(), df2)


def test_polars_lazyframe_sink_ipc(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.ipc"
    sink = PolarsSinkFeatherWriter(file=file)
    kwargs = sink._get_saving_kwargs()
    metadata = sink.save_data(df)
    df2 = pl.read_ipc(file)

    assert PolarsSinkFeatherWriter.applicable_types() == [pl.LazyFrame]
    assert file.exists()
    assert kwargs["compression"] == "uncompressed"
    assert metadata["file_metadata"]["path"] == str(file)
    assert_frame_equal(df.collect(), df2)


def test_polars_lazyframe_sink_ipc_custom_kwargs(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    """Test that non-default kwargs are passed through correctly."""
    file = tmp_path / "test.ipc"
    sink = PolarsSinkFeatherWriter(file=file, compression="lz4", maintain_order=False)
    kwargs = sink._get_saving_kwargs()
    sink.save_data(df)
    df2 = pl.read_ipc(file)

    assert kwargs["compression"] == "lz4"
    assert kwargs["maintain_order"] is False
    assert file.exists()
    assert_frame_equal(df.collect().sort(["a", "b"]), df2.sort(["a", "b"]))


def test_polars_lazyframe_sink_ndjson(df: pl.LazyFrame, tmp_path: pathlib.Path) -> None:
    file = tmp_path / "test.ndjson"
    sink = PolarsSinkNDJSONWriter(file=file)
    kwargs = sink._get_saving_kwargs()
    metadata = sink.save_data(df)
    df2 = pl.read_ndjson(file)

    assert PolarsSinkNDJSONWriter.applicable_types() == [pl.LazyFrame]
    assert file.exists()
    assert kwargs["maintain_order"] is True
    assert metadata["file_metadata"]["path"] == str(file)
    assert_frame_equal(df.collect(), df2)


def test_polars_lazyframe_sink_ndjson_custom_kwargs(
    df: pl.LazyFrame, tmp_path: pathlib.Path
) -> None:
    """Test that non-default kwargs are passed through correctly."""
    file = tmp_path / "test.ndjson"
    sink = PolarsSinkNDJSONWriter(file=file, maintain_order=False)
    kwargs = sink._get_saving_kwargs()
    sink.save_data(df)
    df2 = pl.read_ndjson(file)

    assert kwargs["maintain_order"] is False
    assert file.exists()
    assert_frame_equal(df.collect().sort(["a", "b"]), df2.sort(["a", "b"]))


def test_polars_lazyframe_sink_feather_adapter_name() -> None:
    """Test that PolarsSinkFeatherWriter is registered under 'feather', not 'ipc'."""
    assert PolarsSinkFeatherWriter.name() == "feather"


def test_polars_lazyframe_sink_csv_adapter_name() -> None:
    """Test that PolarsSinkCSVWriter is registered under 'csv'."""
    assert PolarsSinkCSVWriter.name() == "csv"


def test_polars_lazyframe_sink_parquet_adapter_name() -> None:
    """Test that PolarsSinkParquetWriter is registered under 'parquet'."""
    assert PolarsSinkParquetWriter.name() == "parquet"


def test_polars_lazyframe_sink_ndjson_adapter_name() -> None:
    """Test that PolarsSinkNDJSONWriter is registered under 'ndjson'."""
    assert PolarsSinkNDJSONWriter.name() == "ndjson"


@pytest.mark.parametrize(
    ("adapter_name", "expected_saver"),
    [
        ("csv", PolarsSinkCSVWriter),
        ("parquet", PolarsSinkParquetWriter),
        ("feather", PolarsSinkFeatherWriter),
        ("ndjson", PolarsSinkNDJSONWriter),
    ],
)
def test_lazyframe_sink_registry_resolution(adapter_name, expected_saver) -> None:
    """Each format resolves one LazyFrame saver, independent of registration order."""
    registered_savers = registry.SAVER_REGISTRY[adapter_name]
    applicable_savers = [saver for saver in registered_savers if saver.applies_to(pl.LazyFrame)]

    assert applicable_savers == [expected_saver]
    assert resolve_adapter_class(pl.LazyFrame, registered_savers) is expected_saver
    assert resolve_adapter_class(pl.LazyFrame, list(reversed(registered_savers))) is expected_saver


@pytest.mark.parametrize(
    ("eager_saver", "streaming_saver"),
    [
        (Pre1PolarsCSVWriter, PolarsSinkCSVWriter),
        (Pre1PolarsParquetWriter, PolarsSinkParquetWriter),
        (Pre1PolarsFeatherWriter, PolarsSinkFeatherWriter),
    ],
)
def test_pre_1_0_lazyframe_sink_resolution_is_unambiguous(eager_saver, streaming_saver) -> None:
    assert eager_saver.applicable_types() == [pl.DataFrame]
    assert resolve_adapter_class(pl.LazyFrame, [eager_saver, streaming_saver]) is streaming_saver
    assert resolve_adapter_class(pl.LazyFrame, [streaming_saver, eager_saver]) is streaming_saver


def test_lazyframe_sink_csv_complete_kwargs(tmp_path: pathlib.Path) -> None:
    sink = PolarsSinkCSVWriter(
        file=tmp_path / "output.csv",
        include_bom=True,
        decimal_comma=True,
        storage_options={"key": "value"},
        extra_kwargs={"retries": 7},
    )

    assert sink._get_saving_kwargs()["include_bom"] is True
    assert sink._get_saving_kwargs()["decimal_comma"] is True
    assert sink._get_saving_kwargs()["storage_options"] == {"key": "value"}
    assert sink._get_saving_kwargs()["retries"] == 7


def test_lazyframe_sink_materializer_preserves_file_argument(tmp_path: pathlib.Path) -> None:
    """The streaming saver must remain compatible with the existing Polars ``file`` API."""

    def lazy_data() -> pl.LazyFrame:
        return pl.LazyFrame({"a": [1, 2], "b": [3, 4]})

    output_file = tmp_path / "output.csv"
    module = ad_hoc_utils.create_temporary_module(lazy_data)
    dr = driver.Driver({}, module)

    materialization_result, _ = dr.materialize(
        to.csv(id="save_lazy_data", dependencies=["lazy_data"], file=output_file)
    )

    assert materialization_result["save_lazy_data"]["file_metadata"]["path"] == str(output_file)
    assert_frame_equal(pl.read_csv(output_file), lazy_data().collect())
