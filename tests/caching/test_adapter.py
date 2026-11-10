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

import threading
from collections.abc import Callable

import pytest

import hamilton.node
from hamilton.caching import fingerprinting
from hamilton.caching.adapter import (
    CachingBehavior,
    CachingEventType,
    HamiltonCacheAdapter,
)
from hamilton.function_modifiers.metadata import cache as cache_decorator
from hamilton.graph import FunctionGraph
from hamilton.htypes import Collect, Parallelizable


@pytest.fixture
def cache_adapter(tmp_path):
    def foo() -> str:
        return "hello-world"

    run_id = "my-run-id"
    adapter = HamiltonCacheAdapter(path=tmp_path)
    adapter.metadata_store.initialize(run_id)
    adapter._fn_graphs[run_id] = FunctionGraph(
        nodes={"foo": hamilton.node.Node.from_fn(foo)},
        config={},
    )
    adapter.behaviors = {run_id: {"foo": CachingBehavior.DEFAULT}}
    adapter._data_savers = {run_id: []}
    adapter._data_loaders = {run_id: []}
    adapter.run_ids.append(run_id)
    adapter.data_versions = {run_id: {}}
    adapter.code_versions = {run_id: {"foo": "0", "bar": "0"}}
    adapter.cache_keys = {run_id: {}}
    adapter._logs = {run_id: []}

    yield adapter

    adapter.metadata_store.delete_all()


def test_post_node_execute_set_result(cache_adapter):
    """Adapter should write to cache and repository if it needs to compute the value"""
    node_name = "foo"
    result = 123
    data_version = fingerprinting.hash_value(result)
    run_id = cache_adapter.last_run_id

    assert cache_adapter.data_versions.get(node_name) is None
    assert cache_adapter.result_store.exists(data_version) is False

    cache_adapter.data_versions[run_id][node_name] = data_version
    cache_adapter.post_node_execute(
        run_id=run_id,  # latest run_id
        node_=cache_adapter._fn_graphs[run_id].nodes[node_name],
        kwargs={},
        result=result,
    )

    assert cache_adapter.result_store.exists(data_version)
    assert cache_adapter.result_store.get(data_version=data_version) == result


def test_do_execute_reads_data_version_directly_from_memory(cache_adapter):
    """Adapter shouldn't check the repository if fingerprint is available"""

    def foo() -> int:
        return 123

    cached_result = foo()
    data_version = fingerprinting.hash_value(cached_result)
    run_id = cache_adapter.last_run_id

    cache_adapter.data_versions[run_id]["foo"] = data_version
    cache_adapter.pre_node_execute(run_id=run_id, node_=hamilton.node.Node.from_fn(foo), kwargs={})

    assert not any(
        event.event_type == CachingEventType.GET_DATA_VERSION and event.actor == "metadata_store"
        for event in cache_adapter.logs(run_id)
    )


def test_run_to_execute_repo_cache_desync(cache_adapter):
    """The adapter determines the value is in cache,
    but there's an error loading the value from cache.

    The adapter should delete metadata store keys to force recompute and
    writing the result to cache

    NOTE that this will only log and error and not raise any Exception.
    This is because adapters cannot currently raise Exception that stop
    the main execution.
    """

    def foo() -> int:
        return 123

    run_id = cache_adapter.last_run_id  # latest run_id

    # set data version in memory
    cache_adapter.data_versions[run_id]["foo"] = fingerprinting.hash_value(foo())
    cache_adapter.do_node_execute(run_id=run_id, node_=hamilton.node.Node.from_fn(foo), kwargs={})

    # found data version in memory, but the value wasn't in cache
    # forcing deletion from metadata_store and recompute
    logs = cache_adapter.logs(run_id, level="debug")
    assert any(event.event_type == CachingEventType.MISSING_RESULT for event in logs["foo"])
    assert any(event.event_type == CachingEventType.EXECUTE_NODE for event in logs["foo"])


@pytest.mark.parametrize(
    "behavior",
    [
        "default",
        "recompute",
        "disable",
        "ignore",
    ],
)
def test_cache_tag_resolved(cache_adapter, behavior):
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes["foo"]
    node._tags = {cache_decorator.BEHAVIOR_KEY: behavior}
    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(node)
    assert resolved_behavior == CachingBehavior.from_string(behavior)


def test_default_behavior(cache_adapter):
    h_node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes["foo"]
    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(h_node)
    assert resolved_behavior == CachingBehavior.DEFAULT


def test_driver_behavior_overrides_cache_tag(cache_adapter):
    node_name = "foo"
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes[node_name]
    node._tags = {cache_decorator.BEHAVIOR_KEY: "recompute"}

    resolved_behavior = HamiltonCacheAdapter._resolve_node_behavior(node=node, disable=[node_name])

    assert resolved_behavior == CachingBehavior.DISABLE


def test_raise_if_multiple_driver_behavior_for_same_node(cache_adapter):
    node_name = "foo"
    node = cache_adapter._fn_graphs[cache_adapter.last_run_id].nodes[node_name]

    with pytest.raises(ValueError):
        HamiltonCacheAdapter._resolve_node_behavior(
            node,
            disable=[node_name],
            recompute=[node_name],
        )


# --- lost update between two mapped tasks writing for the same node ---------------------------
#
# For a node inside a mapped block (between a ``Parallelizable`` node and its ``Collect`` node),
# the entry of ``data_versions[run_id]`` and ``cache_keys[run_id]`` is a dictionary keyed by task.
# Two tasks on two threads share one adapter (``MultiThreadingExecutor``), so both may find that
# dictionary missing. If each then creates its own, the second replaces the first and the first
# task's entry is lost. Running threads many times does not reach that order, so the tests below
# force it: both writers are parked right after they observe the missing dictionary, then they
# are resumed one at a time. A writer that gets or creates the dictionary in one atomic step
# never observes it missing, so it has nothing to park on and simply finishes.

MAPPED_NODE = "inside"
TASK_IDS = ("expand-inside.0.inside", "expand-inside.1.inside")
FORCED_SCHEDULE_ATTEMPTS = 80
# Only bounds how long a broken run can hang; the order of the writers never depends on it.
FAILSAFE_TIMEOUT_SECONDS = 30


class _Writer:
    """One mapped task writing to the adapter on its own thread."""

    def __init__(self, write: Callable[[], None]):
        self._write = write
        self.error: BaseException | None = None
        self.parked_or_done = threading.Event()
        self.resume = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        try:
            self._write()
        except BaseException as e:
            self.error = e
        finally:
            self.parked_or_done.set()

    def park(self) -> None:
        self.parked_or_done.set()
        self.resume.wait(FAILSAFE_TIMEOUT_SECONDS)


class _ParkOnMissing(dict):
    """Per-run map that parks a writer thread right after it observes that ``watched_key`` is missing.

    Every way of asking whether the key is there is covered (``.get()``, ``in``, ``[]``),
    so that the schedule is forced for any check-then-create sequence, not only the current one.
    """

    def __init__(self, watched_key: str, writers: dict[threading.Thread, _Writer]):
        super().__init__()
        self._watched_key = watched_key
        self._writers = writers

    def _park_if_missing(self, key: str, found: bool) -> None:
        """Called once the lookup is done, so the writer resumes with what it saw before parking."""
        writer = self._writers.get(threading.current_thread())
        if writer is not None and key == self._watched_key and not found:
            writer.park()

    def get(self, key, default=None):
        found = super().__contains__(key)
        value = super().get(key, default)
        self._park_if_missing(key, found)
        return value

    def __contains__(self, key) -> bool:
        found = super().__contains__(key)
        self._park_if_missing(key, found)
        return found

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            self._park_if_missing(key, found=False)
            raise


def _write_in_losing_order(
    per_run_maps: dict[str, dict], run_id: str, writes: list[Callable[[], None]]
) -> None:
    """Run each of ``writes`` on its own thread: all of them observe that the entry of
    ``MAPPED_NODE`` is missing before any of them creates it, then they finish one after the other.
    """
    writers = [_Writer(write) for write in writes]
    per_run_maps[run_id] = _ParkOnMissing(
        watched_key=MAPPED_NODE, writers={writer.thread: writer for writer in writers}
    )
    for writer in writers:
        writer.thread.start()
    for writer in writers:
        assert writer.parked_or_done.wait(FAILSAFE_TIMEOUT_SECONDS), (
            "A writer neither observed the missing entry nor finished. If writers now wait "
            "for each other before they look the entry up, this test must park them elsewhere."
        )
    for writer in writers:
        writer.resume.set()
        writer.thread.join(FAILSAFE_TIMEOUT_SECONDS)
        assert not writer.thread.is_alive()
        if writer.error is not None:
            raise writer.error


@pytest.fixture
def mapped_cache_adapter(cache_adapter):
    """Adapter whose graph has a standard node and a mapped block: ``expand -> inside -> collect``."""

    def standard() -> int:
        return 1

    def expand() -> Parallelizable[int]:
        yield from range(len(TASK_IDS))

    def inside(expand: int) -> int:
        return expand

    def collect(inside: Collect[int]) -> int:
        return sum(inside)

    run_id = cache_adapter.last_run_id
    cache_adapter._fn_graphs[run_id] = FunctionGraph(
        nodes={
            fn.__name__: hamilton.node.Node.from_fn(fn)
            for fn in (standard, expand, inside, collect)
        },
        config={},
    )
    return cache_adapter


def test_forced_schedule_keeps_data_version_of_each_mapped_task(mapped_cache_adapter):
    adapter = mapped_cache_adapter
    run_id = adapter.last_run_id
    expected = {task_id: f"data-version-of-{task_id}" for task_id in TASK_IDS}

    attempts_that_lost_an_entry = 0
    for _ in range(FORCED_SCHEDULE_ATTEMPTS):
        _write_in_losing_order(
            adapter.data_versions,
            run_id,
            [
                lambda task_id=task_id: adapter._set_memory_metadata(
                    run_id=run_id,
                    node_name=MAPPED_NODE,
                    task_id=task_id,
                    data_version=expected[task_id],
                )
                for task_id in TASK_IDS
            ],
        )
        # read from another thread than the ones that wrote
        read_back = {
            task_id: adapter._get_memory_data_version(
                run_id=run_id, node_name=MAPPED_NODE, task_id=task_id
            )
            for task_id in TASK_IDS
        }
        if read_back != expected or adapter.data_versions[run_id][MAPPED_NODE] != expected:
            attempts_that_lost_an_entry += 1

    assert attempts_that_lost_an_entry == 0, (
        f"lost a data version in {attempts_that_lost_an_entry} of {FORCED_SCHEDULE_ATTEMPTS} attempts"
    )


def test_forced_schedule_keeps_cache_key_of_each_mapped_task(mapped_cache_adapter):
    adapter = mapped_cache_adapter
    run_id = adapter.last_run_id
    expected = {task_id: f"cache-key-of-{task_id}" for task_id in TASK_IDS}

    attempts_that_lost_an_entry = 0
    for _ in range(FORCED_SCHEDULE_ATTEMPTS):
        _write_in_losing_order(
            adapter.cache_keys,
            run_id,
            [
                lambda task_id=task_id: adapter._set_cache_key(
                    run_id=run_id,
                    node_name=MAPPED_NODE,
                    task_id=task_id,
                    cache_key=expected[task_id],
                )
                for task_id in TASK_IDS
            ],
        )
        # read from another thread than the ones that wrote
        read_back = {
            task_id: adapter.get_cache_key(run_id=run_id, node_name=MAPPED_NODE, task_id=task_id)
            for task_id in TASK_IDS
        }
        if read_back != expected or adapter.cache_keys[run_id][MAPPED_NODE] != expected:
            attempts_that_lost_an_entry += 1

    assert attempts_that_lost_an_entry == 0, (
        f"lost a cache key in {attempts_that_lost_an_entry} of {FORCED_SCHEDULE_ATTEMPTS} attempts"
    )


def test_only_nodes_inside_a_mapped_block_are_keyed_by_task(mapped_cache_adapter):
    """Standard, expanding and collecting nodes keep one entry per node, whichever task writes it."""
    adapter = mapped_cache_adapter
    run_id = adapter.last_run_id
    # (node_name, task_id): a task outside of a mapped block has the name of its node as id
    writes = [
        ("standard", None),
        ("standard", "standard"),
        ("expand", "expand"),
        ("collect", "collect"),
        (MAPPED_NODE, TASK_IDS[0]),
        (MAPPED_NODE, TASK_IDS[1]),
    ]

    for node_name, task_id in writes:
        adapter._set_memory_metadata(
            run_id=run_id, node_name=node_name, task_id=task_id, data_version=f"version-{task_id}"
        )
        adapter._set_cache_key(
            run_id=run_id, node_name=node_name, task_id=task_id, cache_key=f"key-{task_id}"
        )

    assert adapter.data_versions[run_id] == {
        "standard": "version-standard",
        "expand": {},  # the expanding node has no data version of its own
        "collect": "version-collect",
        MAPPED_NODE: {task_id: f"version-{task_id}" for task_id in TASK_IDS},
    }
    assert adapter.cache_keys[run_id] == {
        "standard": "key-standard",
        "expand": "key-expand",
        "collect": "key-collect",
        MAPPED_NODE: {task_id: f"key-{task_id}" for task_id in TASK_IDS},
    }
