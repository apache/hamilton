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
from typing import List, Type

import pytest
import yaml

from hamilton.function_modifiers.adapters import resolve_adapter_class
from hamilton.io.data_adapters import DataLoader, DataSaver
from hamilton.plugins.yaml_extensions import PrimitiveTypes, YAMLDataLoader, YAMLDataSaver

TEST_DATA_FOR_YAML = [
    (1, "int.yaml"),
    ("string", "string.yaml"),
    (True, "bool.yaml"),
    ({"key": "value"}, "test.yaml"),
    ([1, 2, 3], "data.yaml"),
    ({"nested": {"a": 1, "b": 2}}, "config.yaml"),
]


@pytest.mark.parametrize("data, file_name", TEST_DATA_FOR_YAML)
def test_yaml_loader(tmp_path: pathlib.Path, data, file_name):
    path = tmp_path / pathlib.Path(file_name)
    with path.open(mode="w") as f:
        yaml.dump(data, f)
    assert path.exists()
    loader = YAMLDataLoader(path)
    loaded_data = loader.load_data(type(data))
    assert loaded_data[0] == data


@pytest.mark.parametrize("data, file_name", TEST_DATA_FOR_YAML)
def test_yaml_saver(tmp_path: pathlib.Path, data, file_name):
    path = tmp_path / pathlib.Path(file_name)
    saver = YAMLDataSaver(path)
    saver.save_data(data)
    assert path.exists()
    with path.open("r") as f:
        loaded_data = yaml.safe_load(f)
    assert data == loaded_data


@pytest.mark.parametrize("data, file_name", TEST_DATA_FOR_YAML)
def test_yaml_loader_and_saver(tmp_path: pathlib.Path, data, file_name):
    path = tmp_path / pathlib.Path(file_name)
    saver = YAMLDataSaver(path)
    saver.save_data(data)
    assert path.exists()
    loader = YAMLDataLoader(path)
    loaded_data = loader.load_data(type(data))
    assert data == loaded_data[0]


@pytest.mark.parametrize(
    "type_,classes,correct_class",
    [(t, [YAMLDataLoader], YAMLDataLoader) for t in PrimitiveTypes],
)
def test_resolve_correct_loader_class(
    type_: Type[Type], classes: List[Type[DataLoader]], correct_class: Type[DataLoader]
):
    assert resolve_adapter_class(type_, classes) == correct_class


@pytest.mark.parametrize(
    "type_,classes,correct_class",
    [(t, [YAMLDataSaver], YAMLDataSaver) for t in PrimitiveTypes],
)
def test_resolve_correct_saver_class(
    type_: Type[Type], classes: List[Type[DataSaver]], correct_class: Type[DataLoader]
):
    assert resolve_adapter_class(type_, classes) == correct_class
