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
import tempfile
from pathlib import Path

import pytest

from hamilton import ad_hoc_utils, driver
from hamilton.caching.stores.file import FileResultStore


def interrupt_writes(monkeypatch, directory):
    original_open = io.open

    def open_with_interruption(file, mode="r", *args, **kwargs):
        stream = original_open(file, mode, *args, **kwargs)
        if "w" in mode and (Path(file).parent == directory or Path(file) == directory):
            original_write = stream.write

            def partial_write(data):
                original_write(data[:1])
                raise OSError("interrupted result write")

            monkeypatch.setattr(stream, "write", partial_write)
        return stream

    monkeypatch.setattr(io, "open", open_with_interruption)
    monkeypatch.setattr("_io.open", open_with_interruption)


@pytest.mark.parametrize("existing", [False, True])
def test_interrupted_write_preserves_result(tmp_path, monkeypatch, existing):
    store = FileResultStore(tmp_path)
    if existing:
        store.set("version", "original")
    with monkeypatch.context() as patch:
        interrupt_writes(patch, tmp_path)
        with pytest.raises(OSError, match="interrupted result write"):
            store.set("version", "replacement")
    if existing:
        assert store.get("version") == "original"
    else:
        assert not store.exists("version")
    assert set(tmp_path.iterdir()) == ({tmp_path / "version"} if existing else set())
    store.set("version", "replacement")
    assert store.get("version") == "replacement"


def test_failed_replace_preserves_result(tmp_path, monkeypatch):
    store = FileResultStore(tmp_path)
    store.set("version", "original")

    def fail_replace(*args, **kwargs):
        raise OSError("replacement failed")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_replace)
        with pytest.raises(OSError, match="replacement failed"):
            store.set("version", "replacement")
    assert store.get("version") == "original"
    assert list(tmp_path.iterdir()) == [tmp_path / "version"]


def test_refresh_retry_after_partial_write(tmp_path, monkeypatch):
    state = [1]

    def changing() -> int:
        return state[0]

    module = ad_hoc_utils.create_temporary_module(changing)

    def build(recompute=False):
        return (
            driver.Builder()
            .with_modules(module)
            .with_cache(path=tmp_path, recompute=["changing"] if recompute else [])
            .build()
        )

    first = build()
    assert first.execute(["changing"]) == {"changing": 1}
    key = first.cache.get_cache_key(first.cache.last_run_id, "changing")
    original_version = first.cache.metadata_store.get(key)
    state[0] = 2
    refresh = build(recompute=True)
    with monkeypatch.context() as patch:
        interrupt_writes(patch, refresh.cache.result_store.path)
        with pytest.raises(Exception, match="interrupted result write"):
            refresh.execute(["changing"])
    assert refresh.cache.metadata_store.get(key) == original_version
    assert refresh.cache.metadata_store.get_run(refresh.cache.last_run_id) == []
    assert build().execute(["changing"]) == {"changing": 1}
    assert build(recompute=True).execute(["changing"]) == {"changing": 2}
    assert build().execute(["changing"]) == {"changing": 2}


def test_expiry_scan_during_result_write(tmp_path, monkeypatch):
    store = FileResultStore(tmp_path)
    store.set("existing", "original")
    original_temporary_file = tempfile.NamedTemporaryFile

    def scan_after_creation(*args, **kwargs):
        temporary_file = original_temporary_file(*args, **kwargs)
        try:
            store.delete_expired()
        except Exception:
            temporary_file.close()
            Path(temporary_file.name).unlink()
            raise
        return temporary_file

    monkeypatch.setattr(tempfile, "NamedTemporaryFile", scan_after_creation)
    store.set("new", "replacement")
    assert store.get("existing") == "original"
    assert store.get("new") == "replacement"
    assert set(tmp_path.iterdir()) == {tmp_path / "existing", tmp_path / "new"}


def test_expiry_scan_ignores_abandoned_temporary_result(tmp_path):
    store = FileResultStore(tmp_path)
    abandoned = tmp_path / ".hamilton-interrupted.tmp"
    abandoned.write_bytes(b"partial")
    store.set("valid", "original")
    store.delete_expired()
    assert store.get("valid") == "original"
    assert abandoned.read_bytes() == b"partial"
