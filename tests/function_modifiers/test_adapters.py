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

import dataclasses
from collections import Counter
from typing import Any, Collection, Dict, List, Tuple, Type

import pandas as pd
import pytest

from hamilton import ad_hoc_utils, base, driver, graph, node
from hamilton.function_modifiers import base as fm_base
from hamilton.function_modifiers import extract_fields, save_to, source, value
from hamilton.function_modifiers.adapters import (
    InvalidDecoratorException,
    LoadFromDecorator,
    SaveToDecorator,
    dataloader,
    datasaver,
    load_from,
    resolve_adapter_class,
    resolve_kwargs,
)
from hamilton.function_modifiers.base import DefaultNodeCreator
from hamilton.htypes import custom_subclass_check
from hamilton.io.data_adapters import DataLoader, DataSaver
from hamilton.io.default_data_loaders import JSONDataSaver
from hamilton.registry import LOADER_REGISTRY


def test_default_adapters_are_available():
    assert len(LOADER_REGISTRY) > 0


def test_default_adapters_are_registered_once():
    assert "json" in LOADER_REGISTRY
    count_unique = {
        # we want str() of the class to get the fully qualified class name.
        key: Counter([str(value) for value in values])
        for key, values in LOADER_REGISTRY.items()
    }
    for key, value_ in count_unique.items():
        for impl, count in value_.items():
            assert count == 1, (
                f"Adapter for {key} registered multiple times for {impl}. This should not"
                f" happen, as items should just be registered once."
            )


@dataclasses.dataclass
class MockDataLoader(DataLoader):
    required_param: int
    required_param_2: int
    required_param_3: str
    default_param: int = 4
    default_param_2: int = 5
    default_param_3: str = "6"

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    def load_data(self, type_: Type[int]) -> Tuple[int, Dict[str, Any]]:
        return ..., {"required_param": self.required_param, "default_param": self.default_param}

    @classmethod
    def name(cls) -> str:
        return "mock"


def test_load_from_decorator():
    def fn(data: int) -> int:
        return data

    decorator = LoadFromDecorator(
        [MockDataLoader],
        required_param=value("1"),
        required_param_2=value("2"),
        required_param_3=value("3"),
    )
    nodes_raw = DefaultNodeCreator().generate_nodes(fn, {})
    nodes = decorator.transform_dag(nodes_raw, {}, fn)
    assert len(nodes) == 3
    nodes_by_name = {node_.name: node_ for node_ in nodes}
    assert len(nodes_by_name) == 3
    assert "fn" in nodes_by_name
    assert nodes_by_name["fn.load_data.data"].tags == {
        "hamilton.data_loader.source": "mock",
        "hamilton.data_loader": True,
        "hamilton.data_loader.has_metadata": True,
        "hamilton.data_loader.node": "data",
        "hamilton.data_loader.classname": MockDataLoader.__qualname__,
    }
    assert nodes_by_name["fn.select_data.data"].tags == {
        "hamilton.data_loader.source": "mock",
        "hamilton.data_loader": True,
        "hamilton.data_loader.has_metadata": False,
        "hamilton.data_loader.node": "data",
        "hamilton.data_loader.classname": MockDataLoader.__qualname__,
    }


def test_load_from_decorator_resolve_kwargs():
    kwargs = dict(
        required_param=source("1"),
        required_param_2=value(2),
        required_param_3=value("3"),
        default_param=source("4"),
        default_param_2=value(5),
    )

    dependency_kwargs, literal_kwargs = resolve_kwargs(kwargs)
    assert dependency_kwargs == {"required_param": "1", "default_param": "4"}
    assert literal_kwargs == {"required_param_2": 2, "required_param_3": "3", "default_param_2": 5}


def test_load_from_decorator_resolve_kwargs_with_literals():
    kwargs = dict(
        required_param=source("1"),
        required_param_2=2,
        required_param_3="3",
        default_param=source("4"),
        default_param_2=5,
    )

    dependency_kwargs, literal_kwargs = resolve_kwargs(kwargs)
    assert dependency_kwargs == {"required_param": "1", "default_param": "4"}
    assert literal_kwargs == {"required_param_2": 2, "required_param_3": "3", "default_param_2": 5}


def test_load_from_decorator_validate_succeeds():
    decorator = LoadFromDecorator(
        [MockDataLoader],
        required_param=source("1"),
        required_param_2=value(2),
        required_param_3=value("3"),
    )

    def fn(injected_data: int) -> int:
        return injected_data

    decorator.validate(fn)


def test_load_from_decorator_validate_succeeds_with_inject():
    decorator = LoadFromDecorator(
        [MockDataLoader],
        inject_="injected_data",
        required_param=source("1"),
        required_param_2=value(2),
        required_param_3=value("3"),
    )

    def fn(injected_data: int, dependent_data: int) -> int:
        return injected_data + dependent_data

    decorator.validate(fn)


def test_load_from_decorator_validate_fails_dont_know_which_param_to_inject():
    decorator = LoadFromDecorator(
        [MockDataLoader],
        required_param=source("1"),
        required_param_2=value(2),
        required_param_3=value("3"),
    )

    def fn(injected_data: int, other_possible_injected_data: int) -> int:
        return injected_data + other_possible_injected_data

    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn)


def test_load_from_decorator_validate_fails_inject_not_in_fn():
    decorator = LoadFromDecorator(
        [MockDataLoader],
        inject_="injected_data",
        required_param=source("1"),
        required_param_2=value(2),
        required_param_3=value("3"),
    )

    def fn(dependent_data: int) -> int:
        return dependent_data

    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn)


def test_load_from_decorator_validate_fails_inject_missing_param():
    decorator = LoadFromDecorator(
        [MockDataLoader],
        required_param=source("1"),
        required_param_2=value(2),
        # This is commented out cause it'll be missing
        # required_param_3=value("3"),
    )

    def fn(data: int) -> int:
        return data

    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn)


@dataclasses.dataclass
class StringDataLoader(DataLoader):
    def load_data(self, type_: Type) -> Tuple[str, Dict[str, Any]]:
        return "foo", {"loader": "string_data_loader"}

    @classmethod
    def name(cls) -> str:
        return "dummy"

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]


@dataclasses.dataclass
class AnyDataLoader(DataLoader):
    value: Any

    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return self.value, {"loader": "any_data_loader"}

    @classmethod
    def name(cls) -> str:
        return "dummy"

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [Any]


@dataclasses.dataclass
class IntDataLoader(DataLoader):
    def load_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        return 1, {"loader": "int_data_loader"}

    @classmethod
    def name(cls) -> str:
        return "dummy"

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]


@dataclasses.dataclass
class IntDataLoader2(DataLoader):
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    def load_data(self, type_: Type) -> Tuple[int, Dict[str, Any]]:
        return 2, {"loader": "int_data_loader_2"}

    @classmethod
    def name(cls) -> str:
        return "dummy"


def test_validate_fails_incorrect_type():
    decorator = LoadFromDecorator(
        [StringDataLoader, IntDataLoader],
    )

    def fn_str_inject(injected_data: str) -> str:
        return injected_data

    def fn_int_inject(injected_data: int) -> int:
        return injected_data

    def fn_bool_inject(injected_data: bool) -> bool:
        return injected_data

    # This is valid as there is one parameter and its a type that the decorator supports
    decorator.validate(fn_str_inject)

    # This is valid as there is one parameter and its a type that the decorator supports
    decorator.validate(fn_int_inject)

    # This is invalid as there is one parameter and it is not a type that the decorator supports
    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn_bool_inject)


def test_validate_selects_correct_type():
    decorator = LoadFromDecorator(
        [StringDataLoader, IntDataLoader],
    )

    def fn_str_inject(injected_data: str) -> str:
        return injected_data

    def fn_int_inject(injected_data: int) -> int:
        return injected_data

    def fn_bool_inject(injected_data: bool) -> bool:
        return injected_data

    # This is valid as there is one parameter and its a type that the decorator supports
    decorator.validate(fn_str_inject)

    # This is valid as there is one parameter and its a type that the decorator supports
    decorator.validate(fn_int_inject)

    # This is invalid as there is one parameter and it is not a type that the decorator supports
    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn_bool_inject)


# Note that this tests an internal API, but we would like to test this to ensure
# class selection is correct
@pytest.mark.parametrize(
    "type_,classes,correct_class",
    [
        (str, [StringDataLoader, IntDataLoader, IntDataLoader2], StringDataLoader),
        (int, [StringDataLoader, IntDataLoader, IntDataLoader2], IntDataLoader2),
        (int, [IntDataLoader2, IntDataLoader], IntDataLoader),
        (int, [IntDataLoader, IntDataLoader2], IntDataLoader2),
        (int, [StringDataLoader], None),
        (str, [IntDataLoader], None),
        (dict, [IntDataLoader], None),
        (dict, [IntDataLoader, StringDataLoader], None),
        (str, [AnyDataLoader, StringDataLoader], StringDataLoader),
        (dict, [AnyDataLoader, StringDataLoader], AnyDataLoader),
    ],
)
def test_resolve_correct_loader_class(
    type_: Type[Type], classes: List[Type[DataLoader]], correct_class: Type[DataLoader]
):
    assert resolve_adapter_class(type_, classes) == correct_class


def test_decorator_validate():
    decorator = LoadFromDecorator(
        [StringDataLoader, IntDataLoader, IntDataLoader2],
    )

    def fn_str_inject(injected_data: str) -> str:
        return injected_data

    def fn_int_inject(injected_data: int) -> int:
        return injected_data

    def fn_bool_inject(injected_data: bool) -> bool:
        return injected_data

    # This is valid as there is one parameter and its a type that the decorator supports
    decorator.validate(fn_str_inject)
    decorator.validate(fn_int_inject)
    # This is invalid as there is one parameter and it is not a type that the decorator supports
    with pytest.raises(fm_base.InvalidDecoratorException):
        decorator.validate(fn_bool_inject)


# End-to-end tests are probably cleanest
# We've done a bunch of tests of internal structures for other decorators,
# but that leaves the testing brittle
# We don't test the driver, we just use the function_graph to tests the nodes
def test_load_from_decorator_end_to_end():
    @LoadFromDecorator(
        [StringDataLoader, IntDataLoader, IntDataLoader2],
    )
    def fn_str_inject(injected_data: str) -> str:
        return injected_data

    fg = graph.FunctionGraph.from_modules(
        ad_hoc_utils.create_temporary_module(fn_str_inject), config={}
    )
    result = fg.execute(inputs={}, nodes=fg.nodes.values())
    assert result["fn_str_inject"] == "foo"
    assert result["fn_str_inject.load_data.injected_data"] == (
        "foo",
        {"loader": "string_data_loader"},
    )


# End-to-end tests are probably cleanest
# We've done a bunch of tests of internal structures for other decorators,
# but that leaves the testing brittle
# We don't test the driver, we just use the function_graph to tests the nodes
def test_load_from_decorator_end_to_end_with_multiple():
    @LoadFromDecorator(
        [StringDataLoader, IntDataLoader, IntDataLoader2],
        inject_="injected_data_1",
    )
    @LoadFromDecorator(
        [StringDataLoader, IntDataLoader, IntDataLoader2],
        inject_="injected_data_2",
    )
    def fn_str_inject(injected_data_1: str, injected_data_2: int) -> str:
        return "".join([injected_data_1] * injected_data_2)

    fg = graph.FunctionGraph.from_modules(
        ad_hoc_utils.create_temporary_module(fn_str_inject), config={}
    )
    result = fg.execute(inputs={}, nodes=fg.nodes.values())
    assert result["fn_str_inject"] == "foofoo"
    assert result["fn_str_inject.load_data.injected_data_1"] == (
        "foo",
        {"loader": "string_data_loader"},
    )

    assert result["fn_str_inject.load_data.injected_data_2"] == (
        2,
        {"loader": "int_data_loader_2"},
    )


@pytest.mark.parametrize(
    "source_",
    [
        value("tests/resources/data/test_load_from_data.json"),
        source("test_data"),
    ],
)
def test_load_from_decorator_json_file(source_):
    @load_from.json(path=source_)
    def raw_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def number_employees(raw_json_data: Dict[str, Any]) -> int:
        return len(raw_json_data["employees"])

    def sum_age(raw_json_data: Dict[str, Any]) -> float:
        return sum([employee["age"] for employee in raw_json_data["employees"]])

    def mean_age(sum_age: float, number_employees: int) -> float:
        return sum_age / number_employees

    config = {}
    dr = driver.Driver(
        config,
        ad_hoc_utils.create_temporary_module(raw_json_data, number_employees, sum_age, mean_age),
        adapter=base.DefaultAdapter(),
    )
    result = dr.execute(
        ["mean_age"], inputs={"test_data": "tests/resources/data/test_load_from_data.json"}
    )
    assert result["mean_age"] - 32.33333 < 0.0001


def test_loader_fails_for_missing_attribute():
    with pytest.raises(AttributeError):
        load_from.not_a_loader(param=value("foo"))


def test_pandas_extensions_end_to_end(tmp_path_factory):
    output_path = str(tmp_path_factory.mktemp("test_pandas_extensions_end_to_end") / "output.csv")
    input_path = "tests/resources/data/test_load_from_data.csv"

    @save_to.csv(path=source("output_path"), output_name_="save_df")
    @load_from.csv(path=source("input_path"))
    def df(data: pd.DataFrame) -> pd.DataFrame:
        return data

    config = {}
    dr = driver.Driver(
        config,
        ad_hoc_utils.create_temporary_module(df),
        adapter=base.DefaultAdapter(),
    )
    # run once to check that loading is correct
    result = dr.execute(
        ["df", "save_df"],
        inputs={"input_path": input_path, "output_path": output_path},
    )
    assert result["df"].shape == (3, 5)
    assert result["df"].loc[0, "firstName"] == "John"

    #
    result_just_read = dr.execute(
        ["df"],
        inputs={"input_path": output_path},
    )
    # This is just reading the same file we wrote out, so it should be the same
    pd.testing.assert_frame_equal(result["df"], result_just_read["df"])


@dataclasses.dataclass
class MarkingSaver(DataSaver):
    markers: set
    more_markers: set

    def save_data(self, data: int) -> Dict[str, Any]:
        self.markers.add(data)
        self.more_markers.add(data)
        return {}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int, dict]

    @classmethod
    def name(cls) -> str:
        return "marker"


def test_save_to_decorator():
    def fn() -> int:
        return 1

    marking_set = set()
    marking_set_2 = set()
    decorator = SaveToDecorator(
        [MarkingSaver],
        output_name_="save_fn",
        markers=value(marking_set),
        more_markers=source("more_markers"),
    )
    node_ = node.Node.from_fn(fn)
    nodes = decorator.transform_node(node_, {}, fn)
    assert len(nodes) == 2
    nodes_by_name = {node_.name: node_ for node_ in nodes}
    assert "save_fn" in nodes_by_name
    assert "fn" in nodes_by_name
    save_fn_node = nodes_by_name["save_fn"]
    assert sorted(save_fn_node.input_types.keys()) == ["fn", "more_markers"]
    assert save_fn_node(**{"fn": 1, "more_markers": marking_set_2}) == {}
    assert save_fn_node.tags == {
        "hamilton.data_saver": True,
        "hamilton.data_saver.sink": "marker",
        "hamilton.data_saver.classname": MarkingSaver.__qualname__,
    }
    # Check that the markers are updated, ensuring that the save_fn is called
    assert marking_set_2 == {1}
    assert marking_set == {1}


def test_save_to_decorator_with_target():
    @extract_fields({"a": int, "b": int})
    def fn() -> dict:
        return {"a": 1, "b": 2}

    decorator = SaveToDecorator(
        [JSONDataSaver],
        output_name_="save_fn",
        path=value("unused"),
        target_="fn",  # save the original
    )
    node_ = node.Node.from_fn(fn)
    nodes = {n.name: n for n in decorator.transform_node(node_, {}, fn)}
    saver_node = nodes["save_fn"]
    # We just want to make sure it gets the right input
    assert list(saver_node.input_types) == ["fn"]


@dataclasses.dataclass
class DefaultFactoryLoader(DataLoader):
    field_with_factory: int = dataclasses.field(default_factory=int)

    def __post_init__(self):
        self.param2 = self.field_with_factory + 1

    def load_data(self, type_: Type[int]) -> Tuple[int, Dict[str, Any]]:
        return self.param2, {}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    @classmethod
    def name(cls) -> str:
        return "factory"


def test_loader_default_factory_field():
    @LoadFromDecorator([DefaultFactoryLoader])
    def foo(param: int) -> int:
        return param

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(foo),
        config={},
    )
    assert len(fg) == 3
    assert "foo" in fg


@dataclasses.dataclass
class DefaultFactorySaver(DataSaver):
    field_with_factory: int = dataclasses.field(default_factory=int)

    def __post_init__(self):
        self.param2 = self.field_with_factory + 1

    def save_data(self, data: int) -> Dict[str, Any]:
        return {}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    @classmethod
    def name(cls) -> str:
        return "factory"


def test_saver_default_factory_field():
    @SaveToDecorator([DefaultFactorySaver])
    def foo(param: int) -> int:
        return param

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(foo),
        config={},
    )
    assert len(fg) == 3
    assert "foo" in fg


@dataclasses.dataclass
class OptionalParamDataLoader(DataLoader):
    param: int = 1

    def load_data(self, type_: Type[int]) -> Tuple[int, Dict[str, Any]]:
        return self.param, {}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [int]

    @classmethod
    def name(cls) -> str:
        return "optional"


def test_adapters_optional_params():
    @LoadFromDecorator([OptionalParamDataLoader])
    def foo(param: int) -> int:
        return param

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(foo),
        config={},
    )
    assert len(fg) == 3
    assert "foo" in fg


def test_save_to_with_input_from_other_fn():
    # This tests that we can refer to another node in save_to
    def output_path() -> str:
        return "output.json"

    @save_to.json(path=source("output_path"), output_name_="save_fn")
    def fn() -> dict:
        return {"a": 1}

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(output_path, fn),
        config={},
    )

    assert len(fg) == 3


def test_load_from_with_input_from_other_fn():
    # This tests that we can refer to another node in load_from
    def input_path() -> str:
        return "input.json"

    @load_from.json(path=source("input_path"))
    def fn(data: dict) -> dict:
        return data

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(input_path, fn),
        config={},
    )
    assert len(fg) == 4


def test_load_from_with_multiple_inputs():
    # This tests that we can refer to another node in load_from

    @load_from.json(
        path=value("input_1.json"),
        inject_="data1",
    )
    @load_from.json(
        path=value("input_2.json"),
        inject_="data2",
    )
    def fn(data1: dict, data2: dict) -> dict:
        return {**data1, **data2}

    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(fn),
        config={},
    )
    # One filter, one loader for each and the transform function
    assert len(fg) == 5


import sys

if sys.version_info >= (3, 9):
    dict_ = dict
    tuple_ = tuple
else:
    dict_ = Dict
    tuple_ = Tuple


# Mock functions for dataloader & datasaver testing
def correct_dl_function(foo: int) -> tuple_[int, dict_]:
    return 1, {}


def correct_dl_function_with_subscripts(foo: int) -> tuple_[Dict[str, int], Dict[str, str]]:
    return {"a": 1}, {"b": "c"}


def correct_ds_function(data: float) -> dict_:
    return {}


def no_return_annotation_function():
    return 1, {}


def non_tuple_return_function() -> int:
    return 1


def incorrect_tuple_length_function() -> tuple_[int]:
    return (1,)


def incorrect_second_element_function() -> tuple_[int, list]:
    return 1, []


def incorrect_dict_subscript() -> tuple_[int, Dict[int, str]]:
    return 1, {1: "a"}


incorrect_funcs = [
    no_return_annotation_function,
    non_tuple_return_function,
    incorrect_tuple_length_function,
    incorrect_second_element_function,
    incorrect_dict_subscript,
]


@pytest.mark.parametrize("func", incorrect_funcs, ids=[f.__name__ for f in incorrect_funcs])
def test_dl_validate_incorrect_functions(func):
    dl = dataloader()
    with pytest.raises(InvalidDecoratorException):
        dl.validate(func)


@pytest.mark.skipif(
    sys.version_info < (3, 9, 0),
    reason="dataloader not guarenteed to work with subscripted tuples on 3.8",
)
def test_dl_validate_with_correct_function():
    dl = dataloader()
    try:
        dl.validate(correct_dl_function)
    except InvalidDecoratorException:
        # i.e. fail the test if there's an error
        pytest.fail("validate() raised InvalidDecoratorException unexpectedly!")


def test_dl_validate_with_subscripts():
    dl = dataloader()
    try:
        dl.validate(correct_dl_function_with_subscripts)
    except InvalidDecoratorException:
        # i.e. fail the test if there's an error
        pytest.fail("validate() raised InvalidDecoratorException unexpectedly!")


def test_ds_validate_with_correct_function():
    dl = datasaver()
    try:
        dl.validate(correct_ds_function)
    except InvalidDecoratorException:
        # i.e. fail the test if there's an error
        pytest.fail("validate() raised InvalidDecoratorException unexpectedly!")


def test_ds_validate_incorrect_function():
    dl = dataloader()
    with pytest.raises(InvalidDecoratorException):
        dl.validate(non_tuple_return_function)


def test_dataloader():
    annotation = dataloader()
    (node1, node2) = annotation.generate_nodes(correct_dl_function, {})
    assert node1.name == "correct_dl_function.loader"
    assert node1.input_types["foo"][1] == node.DependencyType.REQUIRED
    assert node1.callable(foo=0) == (1, {})
    assert node1.tags == {
        "hamilton.data_loader": True,
        "hamilton.data_loader.classname": "correct_dl_function()",
        "hamilton.data_loader.has_metadata": True,
        "hamilton.data_loader.node": "correct_dl_function",
        "hamilton.data_loader.source": "loader",
        "module": "tests.function_modifiers.test_adapters",
    }
    assert node2.name == "correct_dl_function"
    assert node2.callable(**{"correct_dl_function.loader": (1, {})}) == 1
    assert node2.tags == {
        "hamilton.data_loader": True,
        "hamilton.data_loader.classname": "correct_dl_function()",
        "hamilton.data_loader.has_metadata": False,
        "hamilton.data_loader.node": "correct_dl_function",
        "hamilton.data_loader.source": "correct_dl_function",
    }


def test_dataloader_future_annotations():
    from tests.resources import nodes_with_future_annotation

    fn_to_collect = nodes_with_future_annotation.sample_dataloader
    fg = graph.create_function_graph(
        ad_hoc_utils.create_temporary_module(fn_to_collect),
        config={},
    )
    # the data loaded is a list
    assert custom_subclass_check(fg["sample_dataloader"].type, list)


def test_datasaver():
    annotation = datasaver()
    (node1,) = annotation.generate_nodes(correct_ds_function, {})
    assert node1.name == "correct_ds_function"
    assert node1.input_types["data"][1] == node.DependencyType.REQUIRED
    assert node1.callable(data=0.0) == {}
    assert node1.tags == {
        "hamilton.data_saver": True,
        "hamilton.data_saver.classname": "correct_ds_function()",
        "hamilton.data_saver.sink": "correct_ds_function",
        "module": "tests.function_modifiers.test_adapters",
    }
