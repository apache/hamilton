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
from unittest import mock

import pandas as pd
import pytest

from hamilton import ad_hoc_utils, async_driver, base
from hamilton.lifecycle.base import (
    BasePostGraphConstruct,
    BasePostGraphConstructAsync,
    BasePostGraphExecute,
    BasePostGraphExecuteAsync,
    BasePostNodeExecute,
    BasePostNodeExecuteAsync,
    BasePreGraphExecute,
    BasePreGraphExecuteAsync,
    BasePreNodeExecute,
    BasePreNodeExecuteAsync,
)

from .resources import simple_async_module


async def async_identity(n: int) -> int:
    await asyncio.sleep(0.01)
    return n


@pytest.mark.asyncio
async def test_await_dict_of_coroutines():
    tasks = {n: async_identity(n) for n in range(0, 10)}
    results = await async_driver.await_dict_of_tasks(tasks)
    assert results == {n: await async_identity(n) for n in range(0, 10)}


@pytest.mark.asyncio
async def test_await_dict_of_tasks():
    tasks = {n: asyncio.create_task(async_identity(n)) for n in range(0, 10)}
    results = await async_driver.await_dict_of_tasks(tasks)
    assert results == {n: await async_identity(n) for n in range(0, 10)}


# The following are not parameterized as we need to use the event loop -- fixtures will complicate this
@pytest.mark.asyncio
async def test_process_value_raw():
    assert await async_driver.process_value(1) == 1


@pytest.mark.asyncio
async def test_process_value_coroutine():
    assert await async_driver.process_value(async_identity(1)) == 1


@pytest.mark.asyncio
async def test_process_value_task():
    assert await async_driver.process_value(asyncio.create_task(async_identity(1))) == 1


@pytest.mark.asyncio
async def test_driver_end_to_end():
    dr = async_driver.AsyncDriver({}, simple_async_module)
    all_vars = [var.name for var in dr.list_available_variables() if var.name != "return_df"]
    result = await dr.raw_execute(final_vars=all_vars, inputs={"external_input": 1})
    result["a"] = result["a"].to_dict()  # convert to dict for comparison
    result["b"] = result["b"].to_dict()  # convert to dict for comparison
    assert result == {
        "a": pd.Series([1, 2, 3]).to_dict(),
        "another_async_func": 8,
        "async_func_with_param": 4,
        "b": pd.Series([4, 5, 6]).to_dict(),
        "external_input": 1,
        "non_async_func_with_decorator": {"result_1": 9, "result_2": 5},
        "result_1": 9,
        "result_2": 5,
        "result_3": 1,
        "result_4": 2,
        "return_dict": {"result_3": 1, "result_4": 2},
        "simple_async_func": 2,
        "simple_non_async_func": 7,
    }


@pytest.mark.asyncio
@mock.patch("hamilton.telemetry.send_event_json")
@mock.patch("hamilton.telemetry.g_telemetry_enabled", True)
async def test_driver_end_to_end_telemetry(send_event_json):
    dr = async_driver.AsyncDriver({}, simple_async_module, result_builder=base.DictResult())
    with mock.patch("hamilton.telemetry.g_telemetry_enabled", False):
        # don't count this telemetry tracking invocation
        all_vars = [var.name for var in dr.list_available_variables() if var.name != "return_df"]
    result = await dr.execute(final_vars=all_vars, inputs={"external_input": 1})
    result["a"] = result["a"].to_dict()
    result["b"] = result["b"].to_dict()
    assert result == {
        "a": pd.Series([1, 2, 3]).to_dict(),
        "another_async_func": 8,
        "async_func_with_param": 4,
        "b": pd.Series([4, 5, 6]).to_dict(),
        "external_input": 1,
        "non_async_func_with_decorator": {"result_1": 9, "result_2": 5},
        "result_1": 9,
        "result_2": 5,
        "result_3": 1,
        "result_4": 2,
        "return_dict": {"result_3": 1, "result_4": 2},
        "simple_async_func": 2,
        "simple_non_async_func": 7,
    }
    # to ensure the last telemetry invocation finishes executing
    # get all tasks -- and the current task, and await all others.
    tasks = asyncio.all_tasks()
    current_task = asyncio.current_task()
    await asyncio.gather(*[t for t in tasks if t != current_task])
    assert send_event_json.called
    assert len(send_event_json.call_args_list) == 2


@pytest.mark.asyncio
async def test_async_driver_end_to_end_async_lifecycle_methods():
    tracked_calls = []

    class AsyncTrackingAdapter(
        BasePostGraphConstructAsync,
        BasePreGraphExecuteAsync,
        BasePostGraphExecuteAsync,
        BasePreNodeExecuteAsync,
        BasePostNodeExecuteAsync,
    ):
        def __init__(self, calls: list, pause_time: float = 0.01):
            self.pause_time = pause_time
            self.calls = calls

        async def _pause(self):
            return await asyncio.sleep(self.pause_time)

        async def pre_graph_execute(self, **kwargs):
            await self._pause()
            self.calls.append(("pre_graph_execute", kwargs))

        async def post_graph_execute(self, **kwargs):
            await self._pause()
            self.calls.append(("post_graph_execute", kwargs))

        async def pre_node_execute(self, **kwargs):
            await self._pause()
            self.calls.append(("pre_node_execute", kwargs))

        async def post_node_execute(self, **kwargs):
            await self._pause()
            self.calls.append(("post_node_execute", kwargs))

        async def post_graph_construct(self, **kwargs):
            await self._pause()
            self.calls.append(("post_graph_construct", kwargs))

    adapter = AsyncTrackingAdapter(tracked_calls)

    dr = await async_driver.AsyncDriver(
        {}, simple_async_module, result_builder=base.DictResult(), adapters=[adapter]
    ).ainit()
    all_vars = [var.name for var in dr.list_available_variables() if var.name != "return_df"]
    result = await dr.execute(final_vars=all_vars, inputs={"external_input": 1})
    hooks_called = [call[0] for call in tracked_calls]
    assert set(hooks_called) == {
        "pre_graph_execute",
        "post_graph_execute",
        "pre_node_execute",
        "post_node_execute",
        "post_graph_construct",
    }
    result["a"] = result["a"].to_dict()
    result["b"] = result["b"].to_dict()
    assert result == {
        "a": pd.Series([1, 2, 3]).to_dict(),
        "another_async_func": 8,
        "async_func_with_param": 4,
        "b": pd.Series([4, 5, 6]).to_dict(),
        "external_input": 1,
        "non_async_func_with_decorator": {"result_1": 9, "result_2": 5},
        "result_1": 9,
        "result_2": 5,
        "result_3": 1,
        "result_4": 2,
        "return_dict": {"result_3": 1, "result_4": 2},
        "simple_async_func": 2,
        "simple_non_async_func": 7,
    }


@pytest.mark.asyncio
async def test_async_driver_end_to_end_sync_lifecycle_methods():
    tracked_calls = []

    class AsyncTrackingAdapter(
        BasePostGraphConstruct,
        BasePreGraphExecute,
        BasePostGraphExecute,
        BasePreNodeExecute,
        BasePostNodeExecute,
    ):
        def __init__(self, calls: list, pause_time: float = 0.01):
            self.pause_time = pause_time
            self.calls = calls

        def pre_graph_execute(self, **kwargs):
            self.calls.append(("pre_graph_execute", kwargs))

        def post_graph_execute(self, **kwargs):
            self.calls.append(("post_graph_execute", kwargs))

        def pre_node_execute(self, **kwargs):
            self.calls.append(("pre_node_execute", kwargs))

        def post_node_execute(self, **kwargs):
            self.calls.append(("post_node_execute", kwargs))

        def post_graph_construct(self, **kwargs):
            self.calls.append(("post_graph_construct", kwargs))

    adapter = AsyncTrackingAdapter(tracked_calls)

    dr = await async_driver.AsyncDriver(
        {}, simple_async_module, result_builder=base.DictResult(), adapters=[adapter]
    ).ainit()
    all_vars = [var.name for var in dr.list_available_variables() if var.name != "return_df"]
    result = await dr.execute(final_vars=all_vars, inputs={"external_input": 1})
    hooks_called = [call[0] for call in tracked_calls]
    assert set(hooks_called) == {
        "pre_graph_execute",
        "post_graph_execute",
        "pre_node_execute",
        "post_node_execute",
        "post_graph_construct",
    }
    result["a"] = result["a"].to_dict()
    result["b"] = result["b"].to_dict()
    assert result == {
        "a": pd.Series([1, 2, 3]).to_dict(),
        "another_async_func": 8,
        "async_func_with_param": 4,
        "b": pd.Series([4, 5, 6]).to_dict(),
        "external_input": 1,
        "non_async_func_with_decorator": {"result_1": 9, "result_2": 5},
        "result_1": 9,
        "result_2": 5,
        "result_3": 1,
        "result_4": 2,
        "return_dict": {"result_3": 1, "result_4": 2},
        "simple_async_func": 2,
        "simple_non_async_func": 7,
    }


@pytest.mark.asyncio
async def test_async_driver_overrides():
    # This specifically tests that raw execute does not return
    # and does not compute the non-returned items
    this_list_should_be_empty = []

    async def never_run() -> int:
        this_list_should_be_empty.append("never_run")
        await asyncio.sleep(0.01)
        return 1

    async def overridden(never_run: int) -> int:
        this_list_should_be_empty.append("overridden")
        await asyncio.sleep(0.01)
        return never_run + 1

    async def will_be_run(overridden: int) -> int:
        await asyncio.sleep(0.01)
        return 1 + overridden

    mod = ad_hoc_utils.create_temporary_module(never_run, will_be_run, overridden)
    dr = await async_driver.Builder().with_modules(mod).build()
    # Testing execute as it's a part of the contract and will remain so
    # raw_execute is closer to the error, but don't want to test it instead
    res = await dr.execute(final_vars=["will_be_run"], overrides={"overridden": 3})
    assert len(this_list_should_be_empty) == 0
    assert res == {"will_be_run": 4}


@pytest.mark.asyncio
async def test_async_builder_result_builder_custom():
    def foo() -> int:
        return 1

    mod = ad_hoc_utils.create_temporary_module(foo)
    result_builder = base.PandasDataFrameResult()
    dr = await async_driver.Builder().with_adapters(result_builder).with_modules(mod).build()
    assert isinstance(await dr.execute(final_vars=["foo"]), pd.DataFrame)


@pytest.mark.asyncio
async def test_async_builder_result_builder_default():
    def foo() -> int:
        return 1

    mod = ad_hoc_utils.create_temporary_module(foo)
    dr = await async_driver.Builder().with_modules(mod).build()
    assert (await dr.execute(final_vars=["foo"])) == {"foo": 1}
    # builder.result_builder = result_builder


@pytest.mark.asyncio
async def test_async_builder_without_init():
    def foo() -> int:
        return 1

    class TestLifecycleMethod(BasePostGraphConstructAsync):
        def __init__(self):
            self.ran = False

        async def post_graph_construct(self, **kwargs):
            await asyncio.sleep(0.01)
            self.ran = True

    mod = ad_hoc_utils.create_temporary_module(foo)
    hook = TestLifecycleMethod()
    # non-async
    async_driver.Builder().with_modules(mod).with_adapters(hook).build_without_init()
    assert not hook.ran
    await async_driver.Builder().with_modules(mod).with_adapters(hook).build()
    assert hook.ran

    # builder.result_builder = result_builder


@pytest.mark.asyncio
async def test_async_builder_allow_module_overrides():
    def foo() -> int:
        return 1

    mod1 = ad_hoc_utils.create_temporary_module(foo)

    def foo() -> int:
        return 2

    mod2 = ad_hoc_utils.create_temporary_module(foo)

    # Should raise without .allow_module_overrides()
    with pytest.raises(ValueError) as e:
        await async_driver.Builder().with_modules(mod1, mod2).build()

    assert "Cannot define function foo more than once." in str(e.value)

    # build_without_init should also raise
    with pytest.raises(ValueError) as e:
        async_driver.Builder().with_modules(mod1, mod2).build_without_init()

    assert "Cannot define function foo more than once." in str(e.value)

    # Should not raise with .allow_module_overrides()
    dr = await async_driver.Builder().with_modules(mod1, mod2).allow_module_overrides().build()
    assert (await dr.execute(final_vars=["foo"])) == {"foo": 2}

    # Same with build_without_init
    dr = (
        async_driver.Builder()
        .with_modules(mod1, mod2)
        .allow_module_overrides()
        .build_without_init()
    )
    assert (await dr.execute(final_vars=["foo"])) == {"foo": 2}
