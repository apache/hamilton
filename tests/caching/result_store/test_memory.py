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

import pytest

from hamilton.caching.stores.base import StoredResult
from hamilton.caching.stores.file import FileResultStore
from hamilton.caching.stores.memory import InMemoryResultStore

# `result_store` is imported but not directly used because it's
# a pytest fixture automatically provided to tests
from .test_base import result_store  # noqa: F401

# implementations that in-memory result store can `.persist_to()` and `.load_from()`
PERSISTENT_IMPLEMENTATIONS = [FileResultStore]


def _store_size(memory_store: InMemoryResultStore) -> int:
    return len(memory_store._results)


@pytest.fixture
def memory_store():
    store = InMemoryResultStore()
    assert _store_size(store) == 0
    yield store


def test_set(memory_store):
    data_version = "foo"

    memory_store.set(data_version=data_version, result="bar")

    assert memory_store._results[data_version].value == "bar"
    assert _store_size(memory_store) == 1


def test_exists(memory_store):
    data_version = "foo"
    assert memory_store.exists(data_version) is False

    memory_store.set(data_version=data_version, result="bar")

    assert memory_store.exists(data_version) is True


def test_set_doesnt_produce_duplicates(memory_store):
    data_version = "foo"
    assert not memory_store.exists(data_version)

    memory_store.set(data_version=data_version, result="bar")
    memory_store.set(data_version=data_version, result="bar")

    assert memory_store.exists(data_version)
    assert _store_size(memory_store) == 1


def test_get(memory_store):
    data_version = "foo"
    result = StoredResult(value="bar")
    memory_store._results[data_version] = result
    assert memory_store.exists(data_version)

    retrieved_value = memory_store.get(data_version)

    assert retrieved_value is not None
    assert result.value == retrieved_value
    assert _store_size(memory_store) == 1


def test_get_missing_result_is_none(memory_store):
    result = memory_store.get("foo")
    assert result is None


def test_delete(memory_store):
    data_version = "foo"
    memory_store._results[data_version] = StoredResult(value="bar")
    assert _store_size(memory_store) == 1

    memory_store.delete(data_version)

    assert memory_store._results.get(data_version) is None
    assert _store_size(memory_store) == 0


def test_delete_all(memory_store):
    memory_store._results["foo"] = "foo"
    memory_store._results["bar"] = "bar"
    assert _store_size(memory_store) == 2

    memory_store.delete_all()

    assert _store_size(memory_store) == 0


@pytest.mark.parametrize("result_store", PERSISTENT_IMPLEMENTATIONS, indirect=True)
def test_persist_to(result_store, memory_store):  # noqa: F811
    data_version = "foo"
    result = "bar"

    # set values in-memory
    memory_store.set(data_version=data_version, result=result)

    # values exist in memory, but not in destination
    assert memory_store.get(data_version) == result
    assert result_store.get(data_version) is None

    # persist to destination
    memory_store.persist_to(result_store)
    assert memory_store.get(data_version) == result_store.get(data_version)


@pytest.mark.parametrize("result_store", PERSISTENT_IMPLEMENTATIONS, indirect=True)
def test_load_from(result_store):  # noqa: F811
    data_version = "foo"
    result = "bar"

    # set values in source
    result_store.set(data_version=data_version, result=result)

    # values exist in source
    assert result_store.get(data_version) == result

    memory_store = InMemoryResultStore.load_from(
        result_store=result_store, data_versions=[data_version]
    )
    assert memory_store.get(data_version) == result_store.get(data_version)


def test_load_from_must_have_metadata_store_or_data_versions(tmp_path):
    file_result_store = FileResultStore(tmp_path)
    with pytest.raises(ValueError):
        InMemoryResultStore.load_from(result_store=file_result_store)
