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
from typing import Any, Collection, Dict, List, Optional, Tuple, Type

import pytest

from hamilton import base, graph, node, registry
from hamilton.function_modifiers import load_from, save_to, value
from hamilton.io import materialization
from hamilton.io.data_adapters import DataLoader, DataSaver
from hamilton.io.materialization import (
    Extract,
    ExtractorFactory,
    Materialize,
    MaterializerFactory,
    _ExtractorFactoryProtocol,
    _MaterializerFactoryProtocol,
    from_,
    to,
)
from hamilton.lifecycle import base as lifecycle_base

import tests.resources.cyclic_functions
import tests.resources.test_default_args

global_mock_data_saver_cache = {}


@dataclasses.dataclass
class MockDataSaver(DataSaver):
    storage_key: str
    other_storage_key: Optional[str] = None

    def save_data(self, data: Any) -> Dict[str, Any]:
        global_mock_data_saver_cache[self.storage_key] = data
        if self.other_storage_key is not None:
            global_mock_data_saver_cache[self.other_storage_key] = data
        return {"saved": True}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict]

    @classmethod
    def name(cls) -> str:
        return "mock_for_testing"


@dataclasses.dataclass
class MockDataLoader(DataLoader):
    fixed_data: Any

    def load_data(self, type_: Type[Type]) -> Tuple[Type, Dict[str, Any]]:
        return self.fixed_data, {}

    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict]

    @classmethod
    def name(cls) -> str:
        return "mock_for_testing"


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


def test_materialization_dynamic_property_access():
    json_materializer = Materialize.json
    assert isinstance(
        json_materializer, _MaterializerFactoryProtocol
    )  # It should produce a factory function


def test_extraction_dynamic_property_access():
    json_extractor = Extract.json
    assert isinstance(
        json_extractor, _ExtractorFactoryProtocol
    )  # It should produce a factory function


def test_materializer_factory_generates_nodes_no_builder():
    factory = MaterializerFactory(
        "test_materializer",
        [MockDataSaver],
        dependencies=["only_node"],
        result_builder=None,
        storage_key="test_materializer_factory_generates_nodes_no_builder",
    )

    def only_node() -> dict:
        return {"test_materializer_factory_generates_nodes_no_builder": "ran_correctly"}

    base_node = node.Node.from_fn(only_node)
    fn_graph = graph.FunctionGraph({base_node.name: base_node}, {})
    nodes = factory.generate_nodes(fn_graph)
    assert len(nodes) == 1  # No builder node
    (node_,) = nodes
    # Call, test the side effect as well as the ret val
    res = node_(only_node=only_node())
    assert res == {"saved": True}
    assert (
        global_mock_data_saver_cache["test_materializer_factory_generates_nodes_no_builder"]
        == only_node()
    )


def test_extractor_factory_generates_nodes():
    factory = ExtractorFactory(
        "input_data",
        loaders=[MockDataLoader],
        fixed_data=value({"loaded": True}),
    )

    def test(input_data: dict) -> dict:
        return {"loaded_value": input_data}

    base_node = node.Node.from_fn(test)
    nodes_without_dependencies = graph.update_dependencies(
        {base_node.name: base_node}, lifecycle_base.LifecycleAdapterSet(base.DefaultAdapter())
    )
    fn_graph = graph.FunctionGraph(nodes_without_dependencies, {})
    nodes = factory.generate_nodes(fn_graph)
    nodes_by_name = {node_.name: node_ for node_ in nodes}
    assert "input_data" in nodes_by_name
    input_data_node = nodes_by_name["input_data"]
    assert input_data_node.type == dict  # From above


def test_materializer_factory_generates_nodes_with_builder():
    factory = MaterializerFactory(
        "test_materializer",
        [MockDataSaver],
        dependencies=["first_node", "second_node"],
        result_builder=JoinBuilder(),
        storage_key="test_materializer_factory_generates_nodes_with_builder",
        other_storage_key="test_materializer_factory_generates_nodes_with_builder_second_store",
    )

    def first_node() -> dict:
        return {"test_materializer_factory_generates_nodes_no_builder": "ran_correctly"}

    def second_node() -> dict:
        return {"test_materializer_factory_generates_nodes_no_builder_still": "ran_correctly"}

    base_node_0 = node.Node.from_fn(first_node)
    base_node_1 = node.Node.from_fn(second_node)

    fn_graph = graph.FunctionGraph(
        {"first_node": base_node_0, "second_node": base_node_1}, {}, None
    )
    nodes = factory.generate_nodes(fn_graph)
    assert len(nodes) == 2  # One builder node
    nodes_by_name = {node_.name: node_ for node_ in nodes}
    # Call, test the side effect as well as the ret val
    materializer = nodes_by_name.pop("test_materializer")  # This one has a defined name
    res = materializer(test_materializer_build_result={**first_node(), **second_node()})
    assert res == {"saved": True}
    assert global_mock_data_saver_cache[
        "test_materializer_factory_generates_nodes_with_builder"
    ] == {**first_node(), **second_node()}
    (joiner,) = nodes_by_name.values()
    assert joiner(first_node=first_node(), second_node=second_node()) == {
        **first_node(),
        **second_node(),
    }
    assert global_mock_data_saver_cache[
        "test_materializer_factory_generates_nodes_with_builder_second_store"
    ] == {**first_node(), **second_node()}


def test_modify_function_graph_materializers():
    factory_1 = MaterializerFactory(
        "materializer_1",
        [MockDataSaver],
        dependencies=["first_node", "second_node"],
        result_builder=JoinBuilder(),
        storage_key="test_modify_function_graph_2",
    )

    factory_2 = MaterializerFactory(
        "materializer_2",
        [MockDataSaver],
        dependencies=["first_node", "second_node"],
        result_builder=JoinBuilder(),
        storage_key="test_modify_function_graph_1",
    )

    def first_node() -> dict:
        return {"test_materializer_factory_generates_nodes_no_builder": "ran_correctly"}

    def second_node() -> dict:
        return {"test_materializer_factory_generates_nodes_no_builder_still": "ran_correctly"}

    base_node_0 = node.Node.from_fn(first_node)
    base_node_1 = node.Node.from_fn(second_node)

    fn_graph = graph.FunctionGraph(
        {"first_node": base_node_0, "second_node": base_node_1}, {}, None
    )

    fn_graph_modified = materialization.modify_graph(fn_graph, [factory_1, factory_2], [])
    assert "materializer_1" in fn_graph_modified.nodes
    assert "materializer_2" in fn_graph_modified.nodes
    assert "first_node" in fn_graph_modified.nodes
    assert "second_node" in fn_graph_modified.nodes


# TODO -- add loaders in
def test_modify_function_graph_with_extractor_factories():
    factory_1 = ExtractorFactory(
        "input_data_1", [MockDataLoader], fixed_data={"test_extractor_factory_1": "ran_correctly"}
    )

    factory_2 = ExtractorFactory(
        "input_data_2", [MockDataLoader], fixed_data={"test_extractor_factory_2": "ran_correctly"}
    )

    def first_node(input_data_1: dict) -> dict:
        return {"loaded_result": input_data_1}

    def second_node(input_data_2: dict) -> dict:
        return {"loaded_result": input_data_2}

    base_node_0 = node.Node.from_fn(first_node)
    base_node_1 = node.Node.from_fn(second_node)

    fn_graph = graph.FunctionGraph(
        {"first_node": base_node_0, "second_node": base_node_1}, {}, None
    )

    fn_graph_modified = materialization.modify_graph(fn_graph, [], [factory_1, factory_2])
    assert "input_data_1" in fn_graph_modified.nodes
    assert "input_data_2" in fn_graph_modified.nodes
    res = fn_graph_modified.execute(
        nodes=[fn_graph_modified.nodes["first_node"], fn_graph_modified.nodes["second_node"]]
    )
    assert res["input_data_1"] == {"test_extractor_factory_1": "ran_correctly"}
    assert res["input_data_2"] == {"test_extractor_factory_2": "ran_correctly"}
    assert res["first_node"] == {"loaded_result": {"test_extractor_factory_1": "ran_correctly"}}
    assert res["second_node"] == {"loaded_result": {"test_extractor_factory_2": "ran_correctly"}}


def test_modify_function_graph_with_extractor_factories_override():
    """Tests that if we use an injector as an override, its gets run, and the node its replacing does not"""
    factory = ExtractorFactory(
        "value_to_override", [MockDataLoader], fixed_data={"overwritten_result": True}
    )
    ran = False

    def value_to_override() -> dict:
        nonlocal ran
        ran = True
        return {"overwritten_result": False}

    base_node_0 = node.Node.from_fn(value_to_override)

    fn_graph = graph.FunctionGraph({base_node_0.name: base_node_0}, {}, None)

    fn_graph_modified = materialization.modify_graph(fn_graph, [], [factory])
    assert "value_to_override" in fn_graph_modified.nodes
    assert (
        len(fn_graph_modified.nodes[base_node_0.name].input_types) > 0
    )  # It actually has some as its a loader
    res = fn_graph_modified.execute(nodes=[fn_graph_modified.nodes["value_to_override"]])
    assert res["value_to_override"] == {"overwritten_result": True}
    assert ran is False


def test_sanitize_materializer_dependencies_happy():
    """Tests that we return new objects & appropriately sanitize dependency types - converting them as necessary."""
    factory_1 = MaterializerFactory(
        "materializer_1",
        [MockDataSaver],
        dependencies=[
            tests.resources.test_default_args.A,
            tests.resources.test_default_args.B,
            "C",
        ],
        result_builder=JoinBuilder(),
        storage_key="test_modify_function_graph_2",
    )
    s = {tests.resources.test_default_args.__name__}
    actual = factory_1.sanitize_dependencies(s)
    assert actual.id == factory_1.id
    assert actual.savers == factory_1.savers
    assert actual.result_builder == factory_1.result_builder
    assert actual.dependencies == ["A", "B", "C"]
    assert actual is not factory_1


def test_sanitize_materializer_dependencies_error():
    """Tests that we error when bad cases are encountered."""
    factory_1 = MaterializerFactory(
        "materializer_1",
        [MockDataSaver],
        dependencies=["B", tests.resources.cyclic_functions.A],
        result_builder=JoinBuilder(),
        storage_key="test_modify_function_graph_2",
    )
    with pytest.raises(ValueError):
        s = {tests.resources.test_default_args.__name__}
        factory_1.sanitize_dependencies(s)


def test_dynamic_properties_can_be_registered_after_import_for_saver():
    @dataclasses.dataclass
    class CustomDataSaver(DataSaver):
        def save_data(self, type_: Type[Type]) -> Tuple[Type, Dict[str, Any]]:
            return "value", {}

        @classmethod
        def applicable_types(cls) -> Collection[Type]:
            return [dict]

        @classmethod
        def name(cls) -> str:
            return "testing_unique_key_saver"

    registry.register_adapter(CustomDataSaver)

    materialize_property = Materialize.testing_unique_key_saver
    to_property = to.testing_unique_key_saver
    load_from_property = save_to.testing_unique_key_saver
    assert materialize_property is not None
    assert to_property is not None
    assert load_from_property is not None


def test_dynamic_properties_can_be_registered_after_import_for_loader():
    @dataclasses.dataclass
    class CustomDataLoader(DataLoader):
        def load_data(self, type_: Type[int]) -> Tuple[Type[int], Dict[str, Any]]:
            return int, {}

        @classmethod
        def applicable_types(cls) -> Collection[Type]:
            return [int]

        @classmethod
        def name(cls) -> str:
            return "testing_unique_key_loader"

    registry.register_adapter(CustomDataLoader)

    extract_property = Extract.testing_unique_key_loader
    to_property = from_.testing_unique_key_loader
    load_from_property = load_from.testing_unique_key_loader
    assert extract_property is not None
    assert to_property is not None
    assert load_from_property is not None
