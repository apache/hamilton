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

import logging
from typing import Any

import pandas as pd
import pytest

from hamilton import base
from hamilton.driver import Driver
from hamilton.experimental import h_cache

from tests import nodes


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "a": [1, 2, 3],
            "b": [4, 5, 6],
        }
    )


def _read_write_df_test(df, filepath, read_fn, write_fn):
    write_fn(df, filepath, "test")
    pd.testing.assert_frame_equal(read_fn(pd.DataFrame(), filepath), df)


def test_feather(df, tmp_path):
    _read_write_df_test(df, tmp_path / "file.feather", h_cache.read_feather, h_cache.write_feather)


def test_parquet(df, tmp_path):
    _read_write_df_test(df, tmp_path / "file.parquet", h_cache.read_parquet, h_cache.write_parquet)


def test_pickle(df, tmp_path):
    _read_write_df_test(df, tmp_path / "file.pkl", h_cache.read_pickle, h_cache.write_pickle)


def test_json(tmp_path):
    data = {
        "a": 1,
        "b": 2,
    }
    filepath = tmp_path / "file.json"
    h_cache.write_json(data, filepath, "test")
    assert h_cache.read_json({}, filepath) == data


def test_unknown_format(tmp_path):
    cache_path = str(tmp_path)
    adapter = h_cache.CachingGraphAdapter(cache_path, base.DictResult())
    data = {"a": 1, "b": 2}
    filepath = tmp_path / "file.xyz"
    with pytest.raises(ValueError) as err:
        adapter._write_cache("xyz", data, filepath, "test")
    assert str(err.value) == "invalid cache format: xyz"
    with pytest.raises(ValueError) as err:
        adapter._read_cache("xyz", None, filepath)
    assert str(err.value) == "invalid cache format: xyz"


def test_init_default_readers_writers(tmp_path):
    cache_path = str(tmp_path / "data")
    adapter = h_cache.CachingGraphAdapter(cache_path, base.DictResult())
    assert adapter.writers == {
        "json": h_cache.write_json,
        "feather": h_cache.write_feather,
        "parquet": h_cache.write_parquet,
        "pickle": h_cache.write_pickle,
    }
    assert adapter.readers == {
        "json": h_cache.read_json,
        "feather": h_cache.read_feather,
        "parquet": h_cache.read_parquet,
        "pickle": h_cache.read_pickle,
    }


def read_str(expected_type: Any, filepath: str) -> str:
    with open(filepath, "r", encoding="utf8") as file:
        return file.read()


def write_str(data: str, filepath: str, name: str) -> None:
    with open(filepath, "w", encoding="utf8") as file:
        file.write(data)


def test_caching(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    cache_path = str(tmp_path)
    adapter = h_cache.CachingGraphAdapter(
        cache_path,
        base.DictResult(),
        readers={"str": read_str},
        writers={"str": write_str},
    )
    dr = Driver(
        {"initial": "Hello, World!"},
        nodes,
        adapter=adapter,
    )
    assert dr.execute(["both"])["both"] == {
        "lower": "hello, world!",
        "upper": "HELLO, WORLD!",
    }
    assert {"lowercased", "uppercased", "both"} == {rec.message for rec in caplog.records}

    assert read_str("", str(tmp_path / "lowercased.str")) == "hello, world!"
    assert read_str("", str(tmp_path / "uppercased.str")) == "HELLO, WORLD!"
    assert (
        read_str("", str(tmp_path / "both.json"))
        == '{"lower": "hello, world!", "upper": "HELLO, WORLD!"}'
    )

    caplog.clear()

    assert dr.execute(["both"])["both"] == {
        "lower": "hello, world!",
        "upper": "HELLO, WORLD!",
    }
    assert not {rec.message for rec in caplog.records}

    caplog.clear()

    # now we force-compute one of the dependencies
    adapter = h_cache.CachingGraphAdapter(
        cache_path,
        base.DictResult(),
        readers={"str": read_str},
        writers={"str": write_str},
        force_compute={"lowercased"},
    )
    dr = Driver(
        {"initial": "Hello, World!"},
        nodes,
        adapter=adapter,
    )
    assert dr.execute(["both"])["both"] == {
        "lower": "hello, world!",
        "upper": "HELLO, WORLD!",
    }
    # both the forced node and the node dependent on it is computed
    assert {"lowercased", "both"} == {rec.message for rec in caplog.records}


def test_dispatch(tmp_path, caplog):
    caplog.set_level(logging.INFO)
    cache_path = str(tmp_path)
    adapter = h_cache.CachingGraphAdapter(
        cache_path,
        base.PandasDataFrameResult(),
    )
    dr = Driver(
        {},
        nodes,
        adapter=adapter,
    )
    actual = dr.execute(["combined"])
    expected = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": [7, 8, 9]})
    pd.testing.assert_frame_equal(actual, expected)
    assert {"json df", "json series", "parquet df", "parquet series", "combined"} == {
        rec.message for rec in caplog.records
    }

    pd.testing.assert_frame_equal(
        h_cache.read_json(pd.DataFrame(), str(tmp_path / "my_df.json")), expected[["a", "b"]]
    )
    pd.testing.assert_series_equal(
        h_cache.read_json(pd.Series(), str(tmp_path / "my_series.json")),
        pd.Series([7, 8, 9], name="my_series"),
    )
    pd.testing.assert_frame_equal(
        h_cache.read_parquet(pd.DataFrame(), str(tmp_path / "my_df2.parquet")), expected[["a", "b"]]
    )
    pd.testing.assert_series_equal(
        h_cache.read_parquet(pd.Series(), str(tmp_path / "my_series2.parquet")),
        pd.Series([7, 8, 9], name="my_series2"),
    )

    caplog.clear()
    actual = dr.execute(["combined"])
    pd.testing.assert_frame_equal(actual, expected)
    assert {"combined"} == {rec.message for rec in caplog.records}

    caplog.clear()

    # now we force-compute one of the dependencies
    adapter = h_cache.CachingGraphAdapter(
        cache_path,
        base.PandasDataFrameResult(),
        force_compute={"my_df"},
    )
    dr = Driver(
        {},
        nodes,
        adapter=adapter,
    )
    actual = dr.execute(["combined"])
    pd.testing.assert_frame_equal(actual, expected)
    # both the forced node and the node dependent on it is computed
    assert {"json df", "parquet df", "combined"} == {rec.message for rec in caplog.records}
