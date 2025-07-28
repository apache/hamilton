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

import asyncio
import logging

import pytest

from hamilton import ad_hoc_utils, async_driver, driver
from hamilton.execution import executors

# from hamilton.plugins.h_dask import DaskExecutor   # FIXME: Not available CI (see below)
from hamilton.plugins.h_logging import AsyncLoggingAdapter, LoggingAdapter, get_logger

# from hamilton.plugins.h_ray import RayTaskExecutor  # FIXME: Not available in the CI (see below)
from hamilton.plugins.h_threadpool import FutureAdapter

from . import test_logging_task_nodes


def _split_log_messages(caplog, name):
    debug, info, warning, error = [], [], [], []
    for record in caplog.records:
        if record.name == name:
            if record.levelno == logging.DEBUG:
                debug.append(record.message)
            elif record.levelno == logging.INFO:
                info.append(record.message)
            elif record.levelno == logging.WARNING:
                warning.append(record.message)
            elif record.levelno == logging.ERROR:
                error.append(record.message)
    return debug, info, warning, error


def test_logging_serial_nodes_at_info_level(caplog):
    """Test logging of serial nodes at INFO level - log order matters for this test."""

    name = "test_logging_serial_nodes_at_info_level"
    caplog.set_level(logging.INFO, logger=name)

    def a() -> str:
        return "a"

    def b(a: str) -> str:
        logger = get_logger(name)
        logger.warning("Context aware message")
        return a + " b"

    def c(b: str) -> str:
        return b + " c"

    modules = ad_hoc_utils.create_temporary_module(a, b, c)
    dr = driver.Builder().with_modules(modules).with_adapters(LoggingAdapter(name)).build()
    result = dr.execute(["c"])
    assert result["c"] == "a b c"

    messages = [record.message for record in caplog.records if record.name == name]

    assert messages[0].startswith("Graph run")
    assert messages[1:-1] == [
        "Node 'a' - Finished execution [OK]",
        "Node 'b' - Context aware message",
        "Node 'b' - Finished execution [OK]",
        "Node 'c' - Finished execution [OK]",
    ]
    assert messages[-1].endswith("- Finished graph execution [OK]")

    levels = [record.levelname for record in caplog.records if record.name == name]
    assert levels == ["INFO", "INFO", "WARNING", "INFO", "INFO", "INFO"]


def test_logging_serial_nodes_at_debug_level(caplog):
    """Test logging of serial nodes at DEBUG level - log order matters for this test."""

    name = "test_logging_serial_nodes_at_debug_level"
    caplog.set_level(logging.DEBUG, logger=name)

    def a() -> str:
        return "a"

    def b(a: str) -> str:
        logger = get_logger(name)
        logger.warning("Context aware message")
        return a + " b"

    def c(b: str) -> str:
        return b + " c"

    modules = ad_hoc_utils.create_temporary_module(a, b, c)
    dr = driver.Builder().with_modules(modules).with_adapters(LoggingAdapter(name)).build()

    result = dr.execute(["c"])
    assert result["c"] == "a b c"

    messages = [record.message for record in caplog.records if record.name == name]
    assert messages[0].startswith("Graph run")
    assert messages[1:-1] == [
        "Node 'a' - Starting execution without dependencies",
        "Node 'a' - Finished execution [OK]",
        "Node 'b' - Starting execution with dependencies 'a'",
        "Node 'b' - Context aware message",
        "Node 'b' - Finished execution [OK]",
        "Node 'c' - Starting execution with dependencies 'b'",
        "Node 'c' - Finished execution [OK]",
    ]
    assert messages[-1].endswith("- Finished graph execution [OK]")

    levels = [record.levelname for record in caplog.records if record.name == name]
    assert levels == ["INFO", "DEBUG", "INFO", "DEBUG", "WARNING", "INFO", "DEBUG", "INFO", "INFO"]


@pytest.mark.parametrize("adapter", [None, FutureAdapter])
def test_logging_branching_nodes(caplog, adapter):
    """Test logging of branching nodes at multiple logging levels."""

    name = "test_logging_branching_nodes"
    caplog.set_level(logging.DEBUG, logger=name)

    def a() -> str:
        return "a"

    def b() -> str:
        return "b"

    def c() -> str:
        logger = get_logger(name)
        logger.warning("Context aware message")
        return "c"

    def d(a: str, b: str) -> str:
        return a + " " + b + " d"

    def e(c: str) -> str:
        return c + " e"

    def f(d: str, e: str) -> str:
        return d + " " + e + " f"

    modules = ad_hoc_utils.create_temporary_module(a, b, c, d, e, f)
    adapters = [LoggingAdapter(name)]
    if adapter:
        adapters.append(adapter())
    dr = driver.Builder().with_modules(modules).with_adapters(*adapters).build()

    result = dr.execute(["f"])
    assert result["f"] == "a b d c e f"

    debug, info, warning, _ = _split_log_messages(caplog, name)

    assert info[0].startswith("Graph run")
    assert set(info[1:-1]) == {
        "Node 'a' - Finished execution [OK]",
        "Node 'b' - Finished execution [OK]",
        "Node 'c' - Finished execution [OK]",
        "Node 'd' - Finished execution [OK]",
        "Node 'e' - Finished execution [OK]",
        "Node 'f' - Finished execution [OK]",
    }
    assert info[-1].endswith("- Finished graph execution [OK]")

    assert set(debug) == {
        "Node 'a' - Starting execution without dependencies",
        "Node 'b' - Starting execution without dependencies",
        "Node 'c' - Starting execution without dependencies",
        "Node 'd' - Starting execution with dependencies 'a', 'b'",
        "Node 'e' - Starting execution with dependencies 'c'",
        "Node 'f' - Starting execution with dependencies 'd', 'e'",
    }

    assert len(warning) == 1
    assert warning[0] == "Node 'c' - Context aware message"


def test_logging_async_nodes(caplog):
    """Test logging of async nodes at multiple logging levels."""

    name = "test_logging_async_nodes"
    caplog.set_level(logging.DEBUG, logger=name)

    async def a() -> str:
        return "a"

    async def b() -> str:
        return "b"

    async def c() -> str:
        logger = get_logger(name)
        logger.warning("Context aware message")
        return "c"

    async def d(a: str, b: str) -> str:
        return a + " " + b + " d"

    async def e(c: str) -> str:
        return c + " e"

    async def f(d: str, e: str) -> str:
        return d + " " + e + " f"

    async def run_async(module, name):
        dr = (
            await async_driver.Builder()  # type: ignore
            .with_modules(module)
            .with_adapters(AsyncLoggingAdapter(name))
            .build()
        )
        result = await dr.execute(["f"])
        return result

    module = ad_hoc_utils.create_temporary_module(a, b, c, d, e, f)
    result = asyncio.run(run_async(module, name))

    assert result["f"] == "a b d c e f"

    debug, info, warning, _ = _split_log_messages(caplog, name)

    assert info[0].startswith("Graph run")
    assert set(info[1:-1]) == {
        "Node 'a' - Finished execution [OK]",
        "Node 'b' - Finished execution [OK]",
        "Node 'c' - Finished execution [OK]",
        "Node 'd' - Finished execution [OK]",
        "Node 'e' - Finished execution [OK]",
        "Node 'f' - Finished execution [OK]",
    }
    assert info[-1].endswith("- Finished graph execution [OK]")

    assert set(debug) == {
        "Node 'a' - Submitting async node without dependencies",
        "Node 'b' - Submitting async node without dependencies",
        "Node 'c' - Submitting async node without dependencies",
        "Node 'd' - Submitting async node with dependencies 'a', 'b'",
        "Node 'e' - Submitting async node with dependencies 'c'",
        "Node 'f' - Submitting async node with dependencies 'd', 'e'",
    }

    assert len(warning) == 1
    assert warning[0] == "Node 'c' - Context aware message"


@pytest.mark.parametrize(
    ["executor_type", "executor_args", "check_context"],
    [
        (executors.SynchronousLocalTaskExecutor, {}, True),
        (executors.MultiProcessingExecutor, {"max_tasks": 1}, False),
        (executors.MultiThreadingExecutor, {"max_tasks": 2}, True),
        # (RayTaskExecutor, {}, True),  # FIXME: Not available in the CI environment
        # (DaskExecutor, {"client": None}, False),  # FIXME: Not available in the CI environment
    ],
)
def test_logging_parallel_nodes(caplog, executor_type, executor_args, check_context):
    """Test logging of parallel nodes at multiple logging levels."""

    # NOTE: These test is brittle, as it depends on undocumented names of the expanded tasks.

    name = "test_logging_parallel_nodes"
    caplog.set_level(logging.DEBUG, logger=name)

    # FIXME: dask is not available in the CI environment
    # if executor_type == DaskExecutor:
    #     import dask.distributed

    #     cluster = dask.distributed.LocalCluster(n_workers=5)
    #     client = dask.distributed.Client(cluster)
    #     executor_args["client"] = client

    adapters = [LoggingAdapter(name)]
    dr = (
        driver.Builder()
        .with_modules(test_logging_task_nodes)
        .with_adapters(*adapters)
        .enable_dynamic_execution(allow_experimental_mode=True)
        .with_remote_executor(executor_type(**executor_args))
        .build()
    )

    result = dr.execute(["f"])
    assert result["f"] == 20

    debug, info, warning, _ = _split_log_messages(caplog, name)

    assert info[0].startswith("Graph run")
    assert info[1].endswith("task-based logging is enabled")
    assert info[-1].endswith("- Finished graph execution [OK]")

    assert set(info[2:-1]) == {
        "Task 'b' - Task completed [OK]",
        "Task 'expand-c' - Task completed [OK]",
        "Task 'expand-c.0.block-c' - Task completed [OK]",
        "Task 'expand-c.1.block-c' - Task completed [OK]",
        "Task 'expand-c.2.block-c' - Task completed [OK]",
        "Task 'expand-c.3.block-c' - Task completed [OK]",
        "Task 'expand-c.4.block-c' - Task completed [OK]",
        "Task 'collect-c' - Task completed [OK]",
        "Task 'f' - Task completed [OK]",
    }

    # Note: Certain executors do not log task and node level debug messages (especially if they
    # are not running in the same process as the driver).
    local_debug_log = {
        "Task 'b' - Initializing new task and submitting to executor",
        "Task 'b' - Starting execution",
        "Task 'b' - Starting execution without dependencies",
        "Task 'b' - Node 'b' - Finished execution [OK]",
        "Task 'b' - Finished execution [OK]",
        "Task 'expand-c' - Initializing new task and submitting to executor",
        "Task 'expand-c' - Starting execution of nodes 'c'",
        "Task 'expand-c' - Starting execution with dependencies 'b'",
        "Task 'expand-c' - Node 'c' - Finished execution [OK]",
        "Task 'expand-c' - Finished execution [OK]",
        "Task 'expand-c.0.block-c' - Spawning task and submitting to executor",
        "Task 'expand-c.1.block-c' - Spawning task and submitting to executor",
        "Task 'expand-c.2.block-c' - Spawning task and submitting to executor",
        "Task 'expand-c.3.block-c' - Spawning task and submitting to executor",
        "Task 'expand-c.4.block-c' - Spawning task and submitting to executor",
        "Task 'collect-c' - Initializing new task and submitting to executor",
        "Task 'collect-c' - Starting execution of nodes 'e'",
        "Task 'collect-c' - Starting execution with dependencies 'd'",
        "Task 'collect-c' - Node 'e' - Finished execution [OK]",
        "Task 'collect-c' - Finished execution [OK]",
        "Task 'f' - Initializing new task and submitting to executor",
        "Task 'f' - Starting execution",
        "Task 'f' - Starting execution with dependencies 'e'",
        "Task 'f' - Node 'f' - Finished execution [OK]",
        "Task 'f' - Finished execution [OK]",
    }
    assert local_debug_log.difference(set(debug)) == set()

    if check_context:
        assert set(warning) == {
            "Task 'expand-c.0.block-c' - Context aware message",
            "Task 'expand-c.1.block-c' - Context aware message",
            "Task 'expand-c.2.block-c' - Context aware message",
            "Task 'expand-c.3.block-c' - Context aware message",
            "Task 'expand-c.4.block-c' - Context aware message",
        }


def test_logging_with_inputs(caplog):
    """Test logging of nodes with inputs."""

    name = "test_logging_with_inputs"
    caplog.set_level(logging.DEBUG, logger=name)

    def a(x: str) -> str:
        return x

    modules = ad_hoc_utils.create_temporary_module(a)
    dr = driver.Builder().with_modules(modules).with_adapters(LoggingAdapter(name)).build()

    result = dr.execute(["a"], inputs={"x": "test"})
    assert result["a"] == "test"

    _, info, _, _ = _split_log_messages(caplog, name)

    assert info[1].endswith("Using inputs 'x'")


def test_logging_with_overrides(caplog):
    """Test logging of nodes with overrides."""

    name = "test_logging_with_overrides"
    caplog.set_level(logging.DEBUG, logger=name)

    def a(x: str) -> str:
        return x

    modules = ad_hoc_utils.create_temporary_module(a)
    dr = driver.Builder().with_modules(modules).with_adapters(LoggingAdapter(name)).build()

    result = dr.execute(["a"], overrides={"a": "test"})
    assert result["a"] == "test"

    _, info, _, _ = _split_log_messages(caplog, name)

    assert info[1].endswith("Using overrides 'a'")
