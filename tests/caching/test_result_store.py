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
import pickle
from typing import Any, Collection, Dict, Tuple, Type

import pytest

from hamilton.caching import fingerprinting
from hamilton.caching.stores.base import search_data_adapter_registry
from hamilton.caching.stores.file import FileResultStore
from hamilton.io.data_adapters import DataLoader, DataSaver


@pytest.fixture
def result_store(tmp_path):
    store = FileResultStore(tmp_path / "h-cache")

    yield store

    store.delete_all()


def check_result_store_size(result_store, size: int):
    assert len([p for p in result_store.path.iterdir()]) == size


def test_set(result_store):
    data_version = "foo"
    assert not pathlib.Path(result_store.path, data_version).exists()

    result_store.set(data_version=data_version, result="bar")

    assert pathlib.Path(result_store.path, data_version).exists()
    check_result_store_size(result_store, size=1)


def test_exists(result_store):
    data_version = "foo"
    assert (
        result_store.exists(data_version) == pathlib.Path(result_store.path, data_version).exists()
    )

    result_store.set(data_version=data_version, result="bar")

    assert (
        result_store.exists(data_version) == pathlib.Path(result_store.path, data_version).exists()
    )


def test_set_doesnt_produce_duplicates(result_store):
    data_version = "foo"
    assert not result_store.exists(data_version)

    result_store.set(data_version=data_version, result="bar")
    result_store.set(data_version=data_version, result="bar")

    assert result_store.exists(data_version)
    check_result_store_size(result_store, size=1)


def test_get(result_store):
    data_version = "foo"
    result = "bar"
    pathlib.Path(result_store.path, data_version).open("wb").write(pickle.dumps(result))
    assert result_store.exists(data_version)

    retrieved_value = result_store.get(data_version)

    assert retrieved_value
    assert result == retrieved_value
    check_result_store_size(result_store, size=1)


def test_get_missing_result_is_none(result_store):
    result = result_store.get("foo")
    assert result is None


def test_delete(result_store):
    data_version = "foo"
    result_store.set(data_version, "bar")
    assert pathlib.Path(result_store.path, data_version).exists()
    check_result_store_size(result_store, size=1)

    result_store.delete(data_version)

    assert not pathlib.Path(result_store.path, data_version).exists()
    check_result_store_size(result_store, size=0)


def test_delete_all(result_store):
    result_store.set("foo", "foo")
    result_store.set("bar", "bar")
    check_result_store_size(result_store, size=2)

    result_store.delete_all()

    check_result_store_size(result_store, size=0)


@pytest.mark.parametrize(
    "format,value",
    [
        ("json", {"key1": "value1", "key2": 2}),
        ("pickle", ("value1", "value2", "value3")),
    ],
)
def test_save_and_load_materializer(format, value, result_store):
    saver_cls, loader_cls = search_data_adapter_registry(name=format, type_=type(value))
    data_version = "foo"
    materialized_path = result_store._materialized_path(data_version, saver_cls)

    result_store.set(
        data_version=data_version, result=value, saver_cls=saver_cls, loader_cls=loader_cls
    )
    retrieved_value = result_store.get(data_version)

    assert materialized_path.exists()
    assert fingerprinting.hash_value(value) == fingerprinting.hash_value(retrieved_value)


class FakeParquetSaver(DataSaver):
    def __init__(self, file):
        self.file = file

    def save_data(self, data: Any) -> Dict[str, Any]:
        with open(self.file, "w") as f:
            f.write(str(data))
        return {"meta": "data"}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        pass

    @classmethod
    def name(cls) -> str:
        return "fake_parquet"


class FakeParquetLoader(DataLoader):
    def __init__(self, file):
        self.file = file

    def load_data(self, type_: Type[Type]) -> Tuple[Type, Dict[str, Any]]:
        with open(self.file, "r") as f:
            data = eval(f.read())
        return data, {"meta": data}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        pass

    @classmethod
    def name(cls) -> str:
        return "fake_parquet"


def test_save_and_load_file_in_init(result_store):
    value = {"a": 1}
    saver_cls, loader_cls = (FakeParquetSaver, FakeParquetLoader)
    data_version = "foo"
    materialized_path = result_store._materialized_path(data_version, saver_cls)

    result_store.set(
        data_version=data_version, result=value, saver_cls=saver_cls, loader_cls=loader_cls
    )
    retrieved_value = result_store.get(data_version)

    assert materialized_path.exists()
    assert fingerprinting.hash_value(value) == fingerprinting.hash_value(retrieved_value)


class BadSaver(DataSaver):
    def __init__(self, file123):
        self.file = file123

    def save_data(self, data: Any) -> Dict[str, Any]:
        with open(self.file, "w") as f:
            f.write(str(data))
        return {"meta": "data"}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        pass

    @classmethod
    def name(cls) -> str:
        return "fake_parquet"


class BadLoader(DataLoader):
    def __init__(self, file123):
        self.file = file123

    def load_data(self, type_: Type[Type]) -> Tuple[Type, Dict[str, Any]]:
        with open(self.file, "r") as f:
            data = eval(f.read())
        return data, {"meta": data}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        pass

    @classmethod
    def name(cls) -> str:
        return "fake_parquet"


def test_save_and_load_not_path_not_file_init_error(result_store):
    value = {"a": 1}
    saver_cls, loader_cls = (BadSaver, BadLoader)
    data_version = "foo"
    with pytest.raises(ValueError):
        result_store.set(
            data_version=data_version, result=value, saver_cls=saver_cls, loader_cls=loader_cls
        )
    with pytest.raises(ValueError):
        result_store.set(  # make something store it in the result store
            data_version=data_version,
            result=value,
            saver_cls=FakeParquetSaver,
            loader_cls=loader_cls,
        )
        result_store.get(data_version)
