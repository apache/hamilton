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

import importlib
import json
import math
import sys
from typing import Any, Callable, Dict, List, Type

import pandas as pd
import pytest

from hamilton import ad_hoc_utils, base, driver, settings
from hamilton.base import DefaultAdapter
from hamilton.data_quality.base import DataValidationError, ValidationResult
from hamilton.execution import executors, grouping
from hamilton.function_modifiers import source, value
from hamilton.io.materialization import from_, to

import tests.resources.data_quality
import tests.resources.dynamic_config
import tests.resources.example_module
import tests.resources.overrides
import tests.resources.overrides_from_module
import tests.resources.test_for_materialization


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: driver.Driver({}, tests.resources.data_quality, adapter=DefaultAdapter())),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.data_quality)
            .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_local_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .build()
        ),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_modules(tests.resources.data_quality)
            .build()
        ),
    ],
    ids=["basic_driver", "driver_v2_multithreading", "driver_v2_synchronous"],
)
def test_data_quality_workflow_passes(driver_factory: Callable[[], driver.Driver]):
    dr = driver_factory()
    all_vars = dr.list_available_variables()
    result = dr.execute([var.name for var in all_vars], inputs={"data_quality_should_fail": False})
    dq_nodes = [
        var.name
        for var in all_vars
        if var.tags.get("hamilton.data_quality.contains_dq_results", False)
    ]
    assert len(dq_nodes) == 1
    dq_result = result[dq_nodes[0]]
    assert isinstance(dq_result, ValidationResult)
    assert dq_result.passes is True


@pytest.mark.parametrize(
    "driver_factory",
    [
        (lambda: driver.Driver({}, tests.resources.data_quality)),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.data_quality)
            .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_local_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .build()
        ),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_modules(tests.resources.data_quality)
            .build()
        ),
    ],
    ids=["basic_driver", "driver_v2_multithreading", "driver_v2_synchronous"],
)
def test_data_quality_workflow_fails(driver_factory):
    dr = driver_factory()
    all_vars = dr.list_available_variables()
    with pytest.raises(DataValidationError):
        dr.execute([var.name for var in all_vars], inputs={"data_quality_should_fail": True})


# Adapted from https://stackoverflow.com/questions/41858147/how-to-modify-imported-source-code-on-the-fly
# This is needed to decide whether to import annotations...
def modify_and_import(module_name, package, modification_func):
    spec = importlib.util.find_spec(module_name, package)
    source = spec.loader.get_source(module_name)
    new_source = modification_func(source)
    module = importlib.util.module_from_spec(spec)
    codeobj = compile(new_source, module.__spec__.origin, "exec")
    exec(codeobj, module.__dict__)
    sys.modules[module_name] = module
    return module


@pytest.mark.parametrize(
    "driver_factory,future_import_annotations",
    [
        (lambda modules: driver.Driver({"region": "US"}, *modules), False),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(*modules)
            .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_local_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_config({"region": "US"})
            .build(),
            False,
        ),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"region": "US"})
            .with_modules(*modules)
            .build(),
            False,
        ),
        (lambda modules: driver.Driver({"region": "US"}, *modules), True),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(*modules)
            .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_local_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_config({"region": "US"})
            .build(),
            True,
        ),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_config({"region": "US"})
            .with_modules(*modules)
            .build(),
            True,
        ),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_grouping_strategy(grouping.GroupNodesAllAsOne())
            .with_config({"region": "US"})
            .with_modules(*modules)
            .build(),
            False,
        ),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_grouping_strategy(grouping.GroupNodesByLevel())
            .with_config({"region": "US"})
            .with_modules(*modules)
            .build(),
            False,
        ),
        (
            lambda modules: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .with_grouping_strategy(grouping.GroupNodesIndividually())
            .with_config({"region": "US"})
            .with_modules(*modules)
            .build(),
            False,
        ),
    ],
    ids=[
        "basic_driver_no_future_import",
        "driver_v2_multithreading_no_future_import",
        "driver_v2_synchronous_no_future_import",
        "basic_driver_future_import",
        "driver_v2_multithreading_future_import",
        "driver_v2_synchronous_future_import",
        "driver_v2_group_all_as_one",
        "driver_v2_group_by_level",
        "driver_v2_group_nodes_individually",
    ],
)
def test_smoke_screen_module(driver_factory, future_import_annotations):
    # Monkeypatch the env
    # This tells the smoke screen module whether to use the future import
    modification_func = lambda source: (  # noqa: E731
        "\n".join(["from __future__ import annotations"] + source.splitlines())
        if future_import_annotations
        else source
    )
    module = modify_and_import(
        "tests.resources.smoke_screen_module", tests.resources, modification_func
    )
    dr = driver_factory([module])
    output_columns = [
        "raw_acquisition_cost",
        "pessimistic_net_acquisition_cost",
        "neutral_net_acquisition_cost",
        "optimistic_net_acquisition_cost",
        "series_with_start_date_end_date",
    ]
    res = dr.execute(
        inputs={"date_range": {"start_date": "20200101", "end_date": "20220801"}},
        final_vars=output_columns,
    )
    epsilon = 0.00001
    assert abs(res["raw_acquisition_cost"].mean() - 0.393808) < epsilon
    assert abs(res["pessimistic_net_acquisition_cost"].mean() - 0.420769) < epsilon
    assert abs(res["neutral_net_acquisition_cost"].mean() - 0.405582) < epsilon
    assert abs(res["optimistic_net_acquisition_cost"].mean() - 0.399363) < epsilon
    assert res["series_with_start_date_end_date"].iloc[0] == "date_20200101_date_20220801"


_dynamic_config = {
    "columns_to_sum_map": {
        "ab": ["a", "b"],
        "cd": ["c", "d"],
        "ed": ["e", "d"],
        "ae": ["a", "e"],
        # You can create some crazy self-referential stuff
        "abcd": ["ab", "cd"],
        "abcdcd": ["abcd", "cd"],
    },
    settings.ENABLE_POWER_USER_MODE: True,
}


@pytest.mark.parametrize(
    "driver_factory",
    [
        (
            lambda: driver.Driver(
                _dynamic_config, tests.resources.dynamic_config, adapter=DefaultAdapter()
            )
        ),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.dynamic_config)
            .with_config(_dynamic_config)
            .with_remote_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .with_local_executor(executors.MultiThreadingExecutor(max_tasks=3))
            .build()
        ),
        (
            lambda: driver.Builder()
            .enable_dynamic_execution(allow_experimental_mode=True)
            .with_modules(tests.resources.dynamic_config)
            .with_config(_dynamic_config)
            .with_remote_executor(executors.SynchronousLocalTaskExecutor())
            .with_local_executor(executors.SynchronousLocalTaskExecutor())
            .build()
        ),
    ],
    ids=["basic_driver", "driver_v2_multithreading", "driver_v2_synchronous"],
)
def test_end_to_end_with_dynamic_config(driver_factory):
    dr = driver_factory()
    out = dr.execute(final_vars=list(_dynamic_config["columns_to_sum_map"].keys()))
    assert out["ab"][0] == 2
    assert out["cd"][0] == 2
    assert out["ed"][0] == 2
    assert out["ae"][0] == 2
    assert out["abcd"][0] == 4
    assert out["abcdcd"][0] == 6


class JoinBuilder(base.ResultMixin):
    @staticmethod
    def build_result(**outputs: Dict[str, Any]) -> Any:
        out = {}
        for output in outputs.values():
            out.update(output)
        return out

    def output_type(self) -> Type:
        return dict

    def input_types(self) -> List[Type]:
        return [dict]


def test_materialize_driver_call_end_to_end(tmp_path_factory):
    dr = driver.Driver({}, tests.resources.test_for_materialization)
    path_1 = tmp_path_factory.mktemp("home") / "test_materialize_driver_call_end_to_end_1.json"
    path_2 = tmp_path_factory.mktemp("home") / "test_materialize_driver_call_end_to_end_2.json"

    materialization_result, result = dr.materialize(
        to.json(id="materializer_1", dependencies=["json_to_save_1"], path=path_1),
        to.json(
            id="materializer_2",
            dependencies=["json_to_save_1", "json_to_save_2"],
            path=path_2,
            combine=JoinBuilder(),
        ),
        additional_vars=["json_to_save_1", "json_to_save_2"],
    )
    assert result == {
        "json_to_save_1": tests.resources.test_for_materialization.json_to_save_1(),
        "json_to_save_2": tests.resources.test_for_materialization.json_to_save_2(),
    }
    assert "materializer_1" in materialization_result
    assert "materializer_2" in materialization_result
    with open(path_1) as f_1, open(path_2) as f_2:
        assert json.load(f_1) == tests.resources.test_for_materialization.json_to_save_1()
        assert json.load(f_2) == {
            **tests.resources.test_for_materialization.json_to_save_2(),
            **tests.resources.test_for_materialization.json_to_save_1(),
        }


def test_materialize_and_loaders_end_to_end(tmp_path_factory):
    def processed_data(input_data: dict) -> dict:
        data = input_data.copy()
        data["processed"] = True
        return data

    path_in = tmp_path_factory.mktemp("home") / "unprocessed_data.json"
    path_out = tmp_path_factory.mktemp("home") / "processed_data.json"

    with open(path_in, "w") as f:
        json.dump({"processed": False}, f)

    mod = ad_hoc_utils.create_temporary_module(processed_data)

    dr = driver.Driver({}, mod)

    materialization_result, result = dr.materialize(
        from_.json(target="input_data", path=value(path_in)),
        to.json(
            id="materializer",
            dependencies=["processed_data"],
            path=source("output_path"),
            combine=JoinBuilder(),
        ),
        additional_vars=["processed_data"],
        inputs={"output_path": str(path_out)},
    )
    assert result["processed_data"] == {"processed": True}
    assert "materializer" in materialization_result

    with open(path_out) as f:
        assert json.load(f) == {"processed": True}


def test_materialize_and_loaders_end_to_end_without_additional_vars(tmp_path_factory):
    def processed_data(input_data: dict) -> dict:
        data = input_data.copy()
        data["processed"] = True
        return data

    path_in = tmp_path_factory.mktemp("home") / "unprocessed_data.json"
    path_out = tmp_path_factory.mktemp("home") / "processed_data.json"

    with open(path_in, "w") as f:
        json.dump({"processed": False}, f)

    mod = ad_hoc_utils.create_temporary_module(processed_data)

    dr = driver.Driver({}, mod)

    materialization_result, result = dr.materialize(
        from_.json(target="input_data", path=value(path_in)),
        to.json(
            id="materializer",
            dependencies=["processed_data"],
            path=source("output_path"),
            combine=JoinBuilder(),
        ),
        inputs={"output_path": str(path_out)},
    )
    assert "materializer" in materialization_result

    with open(path_out) as f:
        assert json.load(f) == {"processed": True}


def test_materialize_and_loaders_end_to_end_without_to(tmp_path_factory):
    def processed_data(input_data: dict) -> dict:
        data = input_data.copy()
        data["processed"] = True
        return data

    path_in = tmp_path_factory.mktemp("home") / "unprocessed_data.json"

    with open(path_in, "w") as f:
        json.dump({"processed": False}, f)

    mod = ad_hoc_utils.create_temporary_module(processed_data)

    dr = driver.Driver({}, mod)

    materialization_result, result = dr.materialize(
        from_.json(target="input_data", path=value(path_in)), additional_vars=["processed_data"]
    )
    assert result["processed_data"] == {"processed": True}
    assert "materializer" not in materialization_result


def test_no_materialize_failure(tmp_path_factory):
    def processed_data(input_data: dict) -> dict:
        data = input_data.copy()
        data["processed"] = True
        return data

    path_in = tmp_path_factory.mktemp("home") / "unprocessed_data.json"
    path_out = tmp_path_factory.mktemp("home") / "processed_data.json"

    with open(path_in, "w") as f:
        json.dump({"processed": False}, f)

    mod = ad_hoc_utils.create_temporary_module(processed_data)

    dr = driver.Driver({}, mod)

    with pytest.raises(ValueError):
        dr.materialize(
            from_.json(target="input_data", path=value(path_in)),
            inputs={"output_path": str(path_out)},
        )


def test_driver_validate_with_overrides():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    assert dr.execute(["c"], overrides={"b": 1})["c"] == 2


def test_driver_validate_with_overrides_2():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    assert dr.execute(["d"], overrides={"b": 1})["d"] == 3


def test_driver_validate_module_overrides():
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides, tests.resources.overrides_from_module)
        .with_adapter(base.DefaultAdapter())
        .allow_module_overrides()
        .build()
    )
    assert dr.execute(["d"], overrides={"b": 1})["d"] == 15


def test_driver_extra_inputs_can_be_outputs():
    """Tests that we can request outputs that not in the graph, but are in the inputs."""
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    actual = dr.execute(["d", "e"], inputs={"a": 1, "e": 10})
    assert actual["d"] == 4
    assert actual["e"] == 10
    # validates validate functions
    dr.validate_execution(["d", "e"], inputs={"a": 1, "e": 10})
    dr.validate_materialization(additional_vars=["d", "e"], inputs={"a": 1, "e": 10})
    # Checks dataframe use case
    dr = (
        driver.Builder()
        .with_modules(tests.resources.example_module)
        .with_adapter(base.PandasDataFrameResult())
        .build()
    )
    actual = dr.execute(
        ["avg_3wk_spend", "e"],
        inputs={"spend": pd.Series([1, 1, 1, 1, 1]), "e": pd.Series([10, 10, 10, 10, 10])},
    )
    pd.testing.assert_frame_equal(
        actual,
        pd.DataFrame(
            {
                "avg_3wk_spend": pd.Series([math.nan, math.nan, 1.0, 1.0, 1.0], dtype=float),
                "e": [10, 10, 10, 10, 10],
            }
        ),
    )


def test_driver_v2_extra_inputs_can_be_outputs():
    """Tests that we can request outputs that not in the graph, but are in the inputs."""
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .enable_dynamic_execution(allow_experimental_mode=True)
        .build()
    )
    actual = dr.execute(["d", "e"], inputs={"a": 1, "e": 10})
    assert actual["d"] == 4
    assert actual["e"] == 10


def test_driver_fails_on_outputs_not_in_input():
    """Tests that we fail correctly on outputs that are not in the inputs or the graph."""
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    with pytest.raises(ValueError):
        # f missing
        dr.execute(["d", "f"], inputs={"a": 1})


def test_driver_v2_fails_on_outputs_not_in_input():
    """Tests that we fail correctly on outputs that are not in the inputs or the graph."""
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .enable_dynamic_execution(allow_experimental_mode=True)
        .build()
    )
    with pytest.raises(ValueError):
        # f missing
        dr.execute(["d", "f"], inputs={"a": 1})


def test_driver_v2_inputs_can_be_none():
    """Tests that input can be None and checks will still work."""
    dr = (
        driver.Builder()
        .with_modules(tests.resources.overrides)
        .with_adapter(base.DefaultAdapter())
        .build()
    )
    actual = dr.execute(["d"], inputs=None, overrides={"b": 1})
    assert actual["d"] == 3

    with pytest.raises(ValueError):
        # validate that None doesn't cause issues
        dr.execute(["e"], inputs=None)
