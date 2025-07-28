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
import json
import pathlib

import pytest

from hamilton.io.default_data_loaders import JSONDataLoader, JSONDataSaver, RawFileDataSaverBytes
from hamilton.io.utils import FILE_METADATA


@pytest.mark.parametrize(
    "data",
    [
        b"test",
        io.BytesIO(b"test"),
    ],
)
def test_raw_file_adapter(data, tmp_path: pathlib.Path) -> None:
    path = tmp_path / "test"

    writer = RawFileDataSaverBytes(path=path)
    writer.save_data(data)

    with open(path, "rb") as f:
        data2 = f.read()

    data_processed = data if type(data) is bytes else data.getvalue()
    assert data_processed == data2


@pytest.mark.parametrize(
    "data",
    [
        {"key": "value"},
        [{"key": "value1"}, {"key": "value2"}],
        ["value1", "value2"],
        [0, 1],
    ],
)
def test_json_save_object_and_array(data, tmp_path: pathlib.Path):
    """Test that `from_.json` and `to.json` can handle JSON objects where
    the top-level is an object `{ }` -> dict or an array `[ ]` -> list
    """
    data_path = tmp_path / "data.json"
    saver = JSONDataSaver(path=data_path)

    metadata = saver.save_data(data)
    loaded_data = json.loads(data_path.read_text())

    assert JSONDataSaver.applicable_types() == [dict, list]
    assert data_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(data_path)
    assert data == loaded_data


@pytest.mark.parametrize(
    "data",
    [
        {"key": "value"},
        [{"key": "value1"}, {"key": "value2"}],
        ["value1", "value2"],
        [0, 1],
    ],
)
def test_json_load_object_and_array(data, tmp_path: pathlib.Path):
    """Test that `from_.json` and `to.json` can handle JSON objects where
    the top-level is an object `{ }` -> dict or an array `[ ]` -> list
    """
    data_path = tmp_path / "data.json"
    loader = JSONDataLoader(path=data_path)

    json.dump(data, data_path.open("w"))
    loaded_data, metadata = loader.load_data(type(data))

    assert JSONDataLoader.applicable_types() == [dict, list]
    assert data == loaded_data
