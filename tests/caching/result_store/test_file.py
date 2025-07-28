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
import shutil

import pytest

from hamilton.caching import fingerprinting
from hamilton.caching.stores.base import search_data_adapter_registry
from hamilton.caching.stores.file import FileResultStore


def _store_size(result_store: FileResultStore) -> int:
    return len([p for p in result_store.path.iterdir()])


@pytest.fixture
def file_store(tmp_path):
    store = FileResultStore(path=tmp_path)
    assert _store_size(store) == 0
    yield store

    shutil.rmtree(tmp_path)


def test_set(file_store):
    data_version = "foo"

    file_store.set(data_version=data_version, result="bar")

    assert pathlib.Path(file_store.path, data_version).exists()
    assert _store_size(file_store) == 1


def test_exists(file_store):
    data_version = "foo"
    assert file_store.exists(data_version) == pathlib.Path(file_store.path, data_version).exists()

    file_store.set(data_version=data_version, result="bar")

    assert file_store.exists(data_version) == pathlib.Path(file_store.path, data_version).exists()


def test_set_doesnt_produce_duplicates(file_store):
    data_version = "foo"
    assert not file_store.exists(data_version)

    file_store.set(data_version=data_version, result="bar")
    file_store.set(data_version=data_version, result="bar")

    assert file_store.exists(data_version)
    assert _store_size(file_store) == 1


def test_get(file_store):
    data_version = "foo"
    result = "bar"
    pathlib.Path(file_store.path, data_version).open("wb").write(pickle.dumps(result))
    assert file_store.exists(data_version)

    retrieved_value = file_store.get(data_version)

    assert retrieved_value
    assert result == retrieved_value
    assert _store_size(file_store) == 1


def test_get_missing_result_is_none(file_store):
    result = file_store.get("foo")
    assert result is None


def test_delete(file_store):
    data_version = "foo"
    file_store.set(data_version, "bar")
    assert pathlib.Path(file_store.path, data_version).exists()
    assert _store_size(file_store) == 1

    file_store.delete(data_version)

    assert not pathlib.Path(file_store.path, data_version).exists()
    assert _store_size(file_store) == 0


def test_delete_all(file_store):
    file_store.set("foo", "foo")
    file_store.set("bar", "bar")
    assert _store_size(file_store) == 2

    file_store.delete_all()

    assert _store_size(file_store) == 0


@pytest.mark.parametrize(
    "format,value",
    [
        ("json", {"key1": "value1", "key2": 2}),
        ("pickle", ("value1", "value2", "value3")),
    ],
)
def test_save_and_load_materializer(format, value, file_store):
    saver_cls, loader_cls = search_data_adapter_registry(name=format, type_=type(value))
    data_version = "foo"
    materialized_path = file_store._materialized_path(data_version, saver_cls)

    file_store.set(
        data_version=data_version, result=value, saver_cls=saver_cls, loader_cls=loader_cls
    )
    retrieved_value = file_store.get(data_version)

    assert materialized_path.exists()
    assert fingerprinting.hash_value(value) == fingerprinting.hash_value(retrieved_value)
