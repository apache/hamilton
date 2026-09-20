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
import pickle

import pytest

from hamilton.io.default_data_loaders import (
    JSONDataLoader,
    JSONDataSaver,
    PickleLoader,
    PickleSaver,
    RawFileDataSaverBytes,
    set_pickle_loader_allowlist,
)
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


# Tracks side effects from a malicious pickle payload so we can assert the
# restricted unpickler refused to execute it.
_MALICIOUS_PAYLOAD_RAN = []


def _record_side_effect(marker):
    _MALICIOUS_PAYLOAD_RAN.append(marker)
    return marker


class _MaliciousPayload:
    """Object whose `__reduce__` triggers an arbitrary call at load time."""

    def __reduce__(self):
        return (_record_side_effect, ("pwned",))


@pytest.fixture(autouse=True)
def _clear_pickle_allowlist():
    # Make sure the module-level allowlist does not leak across tests.
    set_pickle_loader_allowlist(None)
    _MALICIOUS_PAYLOAD_RAN.clear()
    yield
    set_pickle_loader_allowlist(None)
    _MALICIOUS_PAYLOAD_RAN.clear()


def test_pickle_roundtrip_without_allowlist_warns(tmp_path: pathlib.Path):
    """Backward-compat path: no allowlist -> load still works but warns."""
    data_path = tmp_path / "obj.pkl"
    payload = {"a": 1, "b": [1, 2, 3]}

    PickleSaver(path=str(data_path)).save_data(payload)
    loader = PickleLoader(path=str(data_path))

    with pytest.warns(UserWarning, match="without an allowlist"):
        loaded, _ = loader.load_data(dict)

    assert loaded == payload


def test_pickle_allowlist_permits_listed_types(tmp_path: pathlib.Path):
    """Legitimate object whose module is on the allowlist roundtrips."""
    data_path = tmp_path / "obj.pkl"
    payload = {"a": 1, "b": [1, 2, 3]}

    PickleSaver(path=str(data_path)).save_data(payload)
    loader = PickleLoader(path=str(data_path), allowlist=[("builtins", "dict")])

    loaded, _ = loader.load_data(dict)
    assert loaded == payload


def test_pickle_allowlist_blocks_malicious_reduce(tmp_path: pathlib.Path):
    """Malicious __reduce__ payload is rejected before side effects occur."""
    data_path = tmp_path / "evil.pkl"
    with open(data_path, "wb") as f:
        pickle.dump(_MaliciousPayload(), f)

    # Allowlist that does NOT include the helper used by the payload.
    loader = PickleLoader(path=str(data_path), allowlist=[("builtins", "dict")])

    with pytest.raises(pickle.UnpicklingError, match="Refusing to load"):
        loader.load_data(object)

    assert _MALICIOUS_PAYLOAD_RAN == []  # side effect did not run


def test_pickle_module_level_allowlist_blocks_malicious(tmp_path: pathlib.Path):
    """Module-level `set_pickle_loader_allowlist` applies to fresh instances."""
    data_path = tmp_path / "evil.pkl"
    with open(data_path, "wb") as f:
        pickle.dump(_MaliciousPayload(), f)

    set_pickle_loader_allowlist([("builtins", "dict")])
    loader = PickleLoader(path=str(data_path))

    with pytest.raises(pickle.UnpicklingError):
        loader.load_data(object)

    assert _MALICIOUS_PAYLOAD_RAN == []


def test_pickle_instance_allowlist_overrides_module_default(tmp_path: pathlib.Path):
    """Per-instance allowlist takes precedence over the module-level one."""
    data_path = tmp_path / "obj.pkl"
    PickleSaver(path=str(data_path)).save_data({"a": 1})

    # Module-level allowlist permits nothing useful, but the instance overrides it.
    set_pickle_loader_allowlist([("nonexistent", "Thing")])
    loader = PickleLoader(path=str(data_path), allowlist=[("builtins", "dict")])

    loaded, _ = loader.load_data(dict)
    assert loaded == {"a": 1}
