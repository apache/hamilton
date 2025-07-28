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

import numpy as np
import pytest

from hamilton.io.utils import FILE_METADATA
from hamilton.plugins.numpy_extensions import NumpyNpyReader, NumpyNpyWriter


@pytest.fixture
def array():
    yield np.ones((3, 3, 3))


def test_numpy_file_writer(array: np.ndarray, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "array.npy"

    writer = NumpyNpyWriter(path=file_path)
    metadata = writer.save_data(array)

    assert file_path.exists()
    assert metadata[FILE_METADATA]["path"] == str(file_path)


def test_numpy_file_reader(array: np.ndarray, tmp_path: pathlib.Path) -> None:
    file_path = tmp_path / "array.npy"
    np.save(file_path, array)

    reader = NumpyNpyReader(path=file_path)
    loaded_array, metadata = reader.load_data(np.ndarray)

    assert np.equal(array, loaded_array).all()
    assert NumpyNpyReader.applicable_types() == [np.ndarray]
