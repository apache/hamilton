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

from hamilton.caching.stores.file import FileResultStore
from hamilton.caching.stores.memory import InMemoryResultStore


def _instantiate_result_store(result_store_cls, tmp_path):
    if result_store_cls == FileResultStore:
        return FileResultStore(path=tmp_path)
    elif result_store_cls == InMemoryResultStore:
        return InMemoryResultStore()
    else:
        raise ValueError(
            f"Class `{result_store_cls}` isn't defined in `_instantiate_metadata_store()`"
        )


@pytest.fixture
def result_store(request, tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("result_store")
    result_store_cls = request.param
    result_store = _instantiate_result_store(result_store_cls, tmp_path)

    yield result_store

    result_store.delete_all()


# NOTE add tests that check properties shared across result store implementations below
