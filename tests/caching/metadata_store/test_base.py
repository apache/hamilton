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

from typing import Dict

import pytest

from hamilton.caching.cache_key import create_cache_key
from hamilton.caching.fingerprinting import hash_value
from hamilton.caching.stores.memory import InMemoryMetadataStore
from hamilton.caching.stores.sqlite import SQLiteMetadataStore
from hamilton.graph_types import hash_source_code

# if you're adding a new `MetadataStore` implementation, add it to this list.
# Your implementation should successfully pass all the tests.
# Implementation-specific tests should be added to `test_{implementation}.py`.
IMPLEMENTATIONS = [SQLiteMetadataStore, InMemoryMetadataStore]


def _instantiate_metadata_store(metadata_store_cls, tmp_path):
    if metadata_store_cls == SQLiteMetadataStore:
        return SQLiteMetadataStore(path=tmp_path)
    elif metadata_store_cls == InMemoryMetadataStore:
        return InMemoryMetadataStore()
    else:
        raise ValueError(
            f"Class `{metadata_store_cls}` isn't defined in `_instantiate_metadata_store()`"
        )


def _mock_cache_key(
    node_name: str = "foo",
    code_version: str = "FOO-1",
    dependencies_data_versions: Dict[str, str] = None,
) -> str:
    """Utility to create a valid cache key from mock values.
    This is helpful because ``code_version`` and ``data_version`` found in ``dependencies_data_versions``
    must respect specific encoding.
    """
    dependencies_data_versions = (
        dependencies_data_versions if dependencies_data_versions is not None else {}
    )
    return create_cache_key(
        node_name=node_name,
        code_version=hash_source_code(code_version),
        dependencies_data_versions={k: hash_value(v) for k, v in dependencies_data_versions},
    )


@pytest.fixture
def metadata_store(request, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("result_store")
    metadata_store_cls = request.param
    metadata_store = _instantiate_metadata_store(metadata_store_cls, tmp_path)

    yield metadata_store


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_initialize_empty(metadata_store):
    metadata_store.initialize(run_id="test-run-id")
    assert metadata_store.size == 0


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_not_empty_after_set(metadata_store):
    cache_key = _mock_cache_key()
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)

    metadata_store.set(
        cache_key=cache_key,
        data_version="foo-a",
        run_id=run_id,
    )

    assert metadata_store.size > 0


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_set_doesnt_produce_duplicates(metadata_store):
    cache_key = _mock_cache_key()
    data_version = "foo-a"
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)

    metadata_store.set(
        cache_key=cache_key,
        data_version=data_version,
        run_id=run_id,
    )
    assert metadata_store.size == 1

    metadata_store.set(
        cache_key=cache_key,
        data_version=data_version,
        run_id=run_id,
    )
    assert metadata_store.size == 1


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_get_miss_returns_none(metadata_store):
    cache_key = _mock_cache_key()
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)

    data_version = metadata_store.get(cache_key=cache_key)

    assert data_version is None


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_set_and_get_with_empty_dependencies(metadata_store):
    cache_key = _mock_cache_key()
    data_version = "foo-a"
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)

    metadata_store.set(
        cache_key=cache_key,
        data_version=data_version,
        run_id=run_id,
    )
    retrieved_data_version = metadata_store.get(cache_key=cache_key)

    assert retrieved_data_version == data_version


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_get_run_ids_returns_ordered_list(metadata_store):
    pre_run_ids = metadata_store.get_run_ids()
    assert pre_run_ids == []

    metadata_store.initialize(run_id="foo")
    metadata_store.initialize(run_id="bar")
    metadata_store.initialize(run_id="baz")

    post_run_ids = metadata_store.get_run_ids()
    assert post_run_ids == ["foo", "bar", "baz"]


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_get_run_results_include_cache_key_and_data_version(metadata_store):
    cache_key = _mock_cache_key()
    data_version = "foo-a"
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)

    metadata_store.set(
        cache_key=cache_key,
        data_version=data_version,
        run_id=run_id,
    )

    run_info = metadata_store.get_run(run_id=run_id)

    assert isinstance(run_info, list)
    assert len(run_info) == 1
    assert isinstance(run_info[0], dict)
    assert run_info[0]["cache_key"] == cache_key
    assert run_info[0]["data_version"] == data_version


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_get_run_returns_empty_list_if_run_started_but_no_execution_recorded(metadata_store):
    run_id = "test-run-id"
    metadata_store.initialize(run_id=run_id)
    run_info = metadata_store.get_run(run_id=run_id)
    assert run_info == []


@pytest.mark.parametrize("metadata_store", IMPLEMENTATIONS, indirect=True)
def test_get_run_raises_error_if_run_id_not_found(metadata_store):
    metadata_store.initialize(run_id="test-run-id")
    with pytest.raises(IndexError):
        metadata_store.get_run(run_id="foo")
