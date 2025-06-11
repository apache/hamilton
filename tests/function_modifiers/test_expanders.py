import sys
from typing import Any, Dict, List, Optional, Tuple, Type, TypedDict

import numpy as np
import pandas as pd
import pytest

import hamilton.function_modifiers
from hamilton import function_modifiers, node
from hamilton.function_modifiers import base, expanders
from hamilton.function_modifiers.dependencies import (
    GroupedDependency,
    GroupedDictDependency,
    GroupedListDependency,
    group,
    source,
    value,
)
from hamilton.htypes import Collect, Parallelizable
from hamilton.node import DependencyType

# TODO: Move/refactor for more general use
skipif = pytest.mark.skipif
prior_to_py39 = {
    "condition": sys.version_info < (3, 9, 0),
    "reason": "Python 3.9+ required for this test",
}
prior_to_py311 = {
    "condition": sys.version_info < (3, 11, 0),
    "reason": "Python 3.11+ required for this test",
}


def test_parametrized_invalid_params():
    annotation = function_modifiers.parameterize_values(
        parameter="non_existant",
        assigned_output={("invalid_node_name", "invalid_doc"): "invalid_value"},
    )

    def no_param_node():
        pass

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(no_param_node)

    def wrong_param_node(valid_value):
        pass

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(wrong_param_node)


def test_parametrized_single_param_breaks_without_docs():
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        function_modifiers.parameterize_values(
            parameter="parameter", assigned_output={"only_node_name": "only_value"}
        )


def test_parametrized_single_param():
    annotation = function_modifiers.parameterize_values(
        parameter="parameter", assigned_output={("only_node_name", "only_doc"): "only_value"}
    )

    def identity(parameter: Any) -> Any:
        return parameter

    nodes = annotation.expand_node(node.Node.from_fn(identity), {}, identity)
    assert len(nodes) == 1
    assert nodes[0].name == "only_node_name"
    assert nodes[0].type == Any
    assert nodes[0].documentation == "only_doc"
    called = nodes[0].callable()
    assert called == "only_value"


def test_parametrized_single_param_expanded():
    annotation = function_modifiers.parameterize_values(
        parameter="parameter",
        assigned_output={("node_name_1", "doc1"): "value_1", ("node_value_2", "doc2"): "value_2"},
    )

    def identity(parameter: Any) -> Any:
        return parameter

    nodes = annotation.expand_node(node.Node.from_fn(identity), {}, identity)
    assert len(nodes) == 2
    called_1 = nodes[0].callable()
    called_2 = nodes[1].callable()
    assert nodes[0].documentation == "doc1"
    assert nodes[1].documentation == "doc2"
    assert called_1 == "value_1"
    assert called_2 == "value_2"


def test_parametrized_with_multiple_params():
    annotation = function_modifiers.parameterize_values(
        parameter="parameter",
        assigned_output={("node_name_1", "doc1"): "value_1", ("node_value_2", "doc2"): "value_2"},
    )

    def identity(parameter: Any, static: Any) -> Any:
        return parameter, static

    nodes = annotation.expand_node(node.Node.from_fn(identity), {}, identity)
    assert len(nodes) == 2
    called_1 = nodes[0].callable(static="static_param")
    called_2 = nodes[1].callable(static="static_param")
    assert called_1 == ("value_1", "static_param")
    assert called_2 == ("value_2", "static_param")


def test_parametrized_input():
    annotation = function_modifiers.parametrized_input(
        parameter="parameter",
        variable_inputs={
            "input_1": ("test_1", "Function with first column as input"),
            "input_2": ("test_2", "Function with second column as input"),
        },
    )

    def identity(parameter: Any, static: Any) -> Any:
        return parameter, static

    nodes = annotation.expand_node(node.Node.from_fn(identity), {}, identity)
    assert len(nodes) == 2
    nodes = sorted(nodes, key=lambda n: n.name)
    assert [n.name for n in nodes] == ["test_1", "test_2"]
    assert set(nodes[0].input_types.keys()) == {"static", "input_1"}
    assert set(nodes[1].input_types.keys()) == {"static", "input_2"}


def test_parametrize_sources_validate_param_name():
    """Tests validate function of parameterize_sources capturing bad param name usage."""
    annotation = function_modifiers.parameterize_sources(
        parameterization={
            "test_1": dict(parameterfoo="input_1"),
        }
    )

    def identity(parameter1: str, parameter2: str, static: str) -> str:
        """Function with {parameter1} as first input"""
        return parameter1 + parameter2 + static

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(identity)


def test_parametrized_inputs_validate_reserved_param():
    """Tests validate function of parameterize_inputs catching reserved param usage."""
    annotation = function_modifiers.parameterize_sources(
        **{
            "test_1": dict(parameter2="input_1"),
        }
    )

    def identity(output_name: str, parameter2: str, static: str) -> str:
        """Function with {parameter2} as second input"""
        return output_name + parameter2 + static

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(identity)


def test_parametrized_inputs_validate_bad_doc_string():
    """Tests validate function of parameterize_inputs catching bad doc string."""
    annotation = function_modifiers.parameterize_sources(
        **{
            "test_1": dict(parameter2="input_1"),
        }
    )

    def identity(output_name: str, parameter2: str, static: str) -> str:
        """Function with {foo} as second input"""
        return output_name + parameter2 + static

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(identity)


def test_parametrized_inputs():
    annotation = function_modifiers.parameterize_sources(
        **{
            "test_1": dict(parameter1="input_1", parameter2="input_2"),
            "test_2": dict(parameter1="input_2", parameter2="input_1"),
        }
    )

    def identity(parameter1: str, parameter2: str, static: str) -> str:
        """Function with {parameter1} as first input"""
        return parameter1 + parameter2 + static

    nodes = annotation.expand_node(node.Node.from_fn(identity), {}, identity)
    assert len(nodes) == 2
    nodes = sorted(nodes, key=lambda n: n.name)
    assert [n.name for n in nodes] == ["test_1", "test_2"]
    assert set(nodes[0].input_types.keys()) == {"static", "input_1", "input_2"}
    assert nodes[0].documentation == "Function with input_1 as first input"
    assert set(nodes[1].input_types.keys()) == {"static", "input_1", "input_2"}
    assert nodes[1].documentation == "Function with input_2 as first input"
    result1 = nodes[0].callable(**{"input_1": "1", "input_2": "2", "static": "3"})
    assert result1 == "123"
    result2 = nodes[1].callable(**{"input_1": "1", "input_2": "2", "static": "3"})
    assert result2 == "213"


def test_invalid_column_extractor():
    annotation = function_modifiers.extract_columns("dummy_column")

    def no_param_node() -> int:
        pass

    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(no_param_node)


def test_extract_columns_invalid_passing_list_to_column_extractor():
    """Ensures that people cannot pass in a list."""
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        function_modifiers.extract_columns(["a", "b", "c"])


def test_extract_columns_empty_args():
    """Tests that we fail on empty arguments."""
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        function_modifiers.extract_columns()


def test_extract_columns_happy():
    """Tests that we are happy with good arguments."""
    function_modifiers.extract_columns(*["a", ("b", "some doc"), "c"])


def test_valid_column_extractor():
    """Tests that things work, and that you can provide optional documentation."""
    annotation = function_modifiers.extract_columns("col_1", ("col_2", "col2_doc"))

    def dummy_df_generator() -> pd.DataFrame:
        """dummy doc"""
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    nodes = list(
        annotation.transform_node(node.Node.from_fn(dummy_df_generator), {}, dummy_df_generator)
    )
    assert len(nodes) == 3
    assert nodes[0] == node.Node(
        name=dummy_df_generator.__name__,
        typ=pd.DataFrame,
        doc_string=dummy_df_generator.__doc__,
        callabl=dummy_df_generator,
        tags={"module": "tests.function_modifiers.test_expanders"},
    )
    assert nodes[1].name == "col_1"
    assert nodes[1].type == pd.Series
    assert nodes[1].documentation == "dummy doc"  # we default to base function doc.
    assert nodes[1].input_types == {
        dummy_df_generator.__name__: (pd.DataFrame, DependencyType.REQUIRED)
    }
    assert nodes[2].name == "col_2"
    assert nodes[2].type == pd.Series
    assert nodes[2].documentation == "col2_doc"
    assert nodes[2].input_types == {
        dummy_df_generator.__name__: (pd.DataFrame, DependencyType.REQUIRED)
    }


def test_column_extractor_fill_with():
    def dummy_df() -> pd.DataFrame:
        """dummy doc"""
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    annotation = function_modifiers.extract_columns("col_3", fill_with=0)
    original_node, extracted_column_node = annotation.transform_node(
        node.Node.from_fn(dummy_df), {}, dummy_df
    )
    original_df = original_node.callable()
    extracted_column = extracted_column_node.callable(dummy_df=original_df)
    pd.testing.assert_series_equal(extracted_column, pd.Series([0, 0, 0, 0]), check_names=False)
    pd.testing.assert_series_equal(
        original_df["col_3"], pd.Series([0, 0, 0, 0]), check_names=False
    )  # it has to be in there now


def test_column_extractor_no_fill_with():
    def dummy_df_generator() -> pd.DataFrame:
        """dummy doc"""
        return pd.DataFrame({"col_1": [1, 2, 3, 4], "col_2": [11, 12, 13, 14]})

    annotation = function_modifiers.extract_columns("col_3")
    nodes = list(
        annotation.transform_node(node.Node.from_fn(dummy_df_generator), {}, dummy_df_generator)
    )
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        nodes[1].callable(dummy_df_generator=dummy_df_generator())


@pytest.mark.parametrize(
    "fields",
    [
        None,  # empty
        "string_input",  # not a dict
        ["string_input"],  # not a dict
        {},  # empty dict
        {1: "string", "field": str},  # invalid dict
        {"field": lambda x: x, "field2": int},  # invalid dict
    ],
)
def test_validate_extract_fields(fields):
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        expanders._validate_extract_fields(fields)


@pytest.mark.parametrize(
    "fields",
    [
        {"field": np.ndarray, "field2": str},
        {"field": dict, "field2": int, "field3": list, "field4": float, "field5": str},
        {"field": List[str]},
        {"field": Dict[str, List[str]]},
    ],
)
def test_extract_fields_constructor_happy(fields):
    """Tests that we are happy with good arguments."""
    expanders._validate_extract_fields(fields)


class MyDict(TypedDict):
    test: int
    test2: str


class MyDictBad(TypedDict):
    test2: str


@pytest.mark.parametrize(
    "return_type",
    [
        dict,
        Dict,
        Dict[str, str],
        Dict[str, Any],
        MyDict,
    ],
)
def test_extract_fields_validate_happy(return_type):
    def return_dict() -> return_type:
        return {}

    annotation = function_modifiers.extract_fields({"test": int})
    annotation.validate(return_dict)


class SomeObject:
    pass


class InheritedObject(SomeObject):
    pass


class MyDictInheritance(TypedDict):
    test: SomeObject
    test2: str


class MyDictInheritanceBadCase(TypedDict):
    test: InheritedObject
    test2: str


def test_extract_fields_validate_happy_inheritance():
    def return_dict() -> MyDictInheritance:
        return {}

    annotation = function_modifiers.extract_fields({"test": InheritedObject})
    annotation.validate(return_dict)


def test_extract_fields_validate_not_subclass():
    def return_dict() -> MyDictInheritanceBadCase:
        return {}

    annotation = function_modifiers.extract_fields({"test": SomeObject})
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(return_dict)


@pytest.mark.parametrize(
    "return_type",
    [(int), (list), (np.ndarray), (pd.DataFrame), (MyDictBad)],
)
def test_extract_fields_validate_errors(return_type):
    def return_dict() -> return_type:
        return {}

    annotation = function_modifiers.extract_fields({"test": int})
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(return_dict)


def test_extract_fields_typeddict_empty_fields():
    def return_dict() -> MyDict:
        return {}

    # don't need fields for TypedDict
    annotation = function_modifiers.extract_fields()
    annotation.validate(return_dict)


def test_extract_fields_typeddict_subset():
    def return_dict() -> MyDict:
        return {}

    # test that a subset of fields is fine
    annotation = function_modifiers.extract_fields({"test2": str})
    annotation.validate(return_dict)


def test_valid_extract_fields():
    """Tests whole extract_fields decorator."""
    annotation = function_modifiers.extract_fields(
        {"col_1": list, "col_2": int, "col_3": np.ndarray}
    )

    def dummy_dict_generator() -> dict:
        """dummy doc"""
        return {"col_1": [1, 2, 3, 4], "col_2": 1, "col_3": np.ndarray([1, 2, 3, 4])}

    nodes = list(
        annotation.transform_node(node.Node.from_fn(dummy_dict_generator), {}, dummy_dict_generator)
    )
    assert len(nodes) == 4
    assert nodes[0] == node.Node(
        name=dummy_dict_generator.__name__,
        typ=dict,
        doc_string=dummy_dict_generator.__doc__,
        callabl=dummy_dict_generator,
        tags={"module": "tests.function_modifiers.test_expanders"},
    )
    assert nodes[1].name == "col_1"
    assert nodes[1].type == list
    assert nodes[1].documentation == "dummy doc"  # we default to base function doc.
    assert nodes[1].input_types == {dummy_dict_generator.__name__: (dict, DependencyType.REQUIRED)}
    assert nodes[2].name == "col_2"
    assert nodes[2].type == int
    assert nodes[2].documentation == "dummy doc"
    assert nodes[2].input_types == {dummy_dict_generator.__name__: (dict, DependencyType.REQUIRED)}
    assert nodes[3].name == "col_3"
    assert nodes[3].type == np.ndarray
    assert nodes[3].documentation == "dummy doc"
    assert nodes[3].input_types == {dummy_dict_generator.__name__: (dict, DependencyType.REQUIRED)}


def test_extract_fields_fill_with():
    def dummy_dict() -> dict:
        """dummy doc"""
        return {"col_1": [1, 2, 3, 4], "col_2": 1, "col_3": np.ndarray([1, 2, 3, 4])}

    annotation = function_modifiers.extract_fields({"col_2": int, "col_4": float}, fill_with=1.0)
    original_node, extracted_field_node, missing_field_node = annotation.transform_node(
        node.Node.from_fn(dummy_dict), {}, dummy_dict
    )
    original_dict = original_node.callable()
    extracted_field = extracted_field_node.callable(dummy_dict=original_dict)
    missing_field = missing_field_node.callable(dummy_dict=original_dict)
    assert extracted_field == 1
    assert missing_field == 1.0


def test_extract_fields_no_fill_with():
    def dummy_dict() -> dict:
        """dummy doc"""
        return {"col_1": [1, 2, 3, 4], "col_2": 1, "col_3": np.ndarray([1, 2, 3, 4])}

    annotation = function_modifiers.extract_fields({"col_4": int})
    nodes = list(annotation.transform_node(node.Node.from_fn(dummy_dict), {}, dummy_dict))
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        nodes[1].callable(dummy_dict=dummy_dict())


def test_unpack_fields_valid_explicit_tuple():
    def dummy() -> Tuple[int, str, int]:
        """dummy doc"""
        return 1, "2", 3

    annotation = function_modifiers.unpack_fields("A", "B", "C")
    annotation.validate(dummy)
    nodes = list(annotation.transform_node(node.Node.from_fn(dummy), {}, dummy))
    assert len(nodes) == 4

    assert nodes[0] == node.Node(
        name=dummy.__name__,
        typ=Tuple[int, str, int],
        doc_string=getattr(dummy, "__doc__", ""),
        callabl=dummy,
        tags={"module": "tests.function_modifiers.test_expanders"},
    )
    assert nodes[1].name == "A"
    assert nodes[1].type == int
    assert nodes[1].documentation == "dummy doc"
    assert nodes[1].input_types == {dummy.__name__: (Tuple[int, str, int], DependencyType.REQUIRED)}
    assert nodes[2].name == "B"
    assert nodes[2].type == str
    assert nodes[2].documentation == "dummy doc"
    assert nodes[2].input_types == {dummy.__name__: (Tuple[int, str, int], DependencyType.REQUIRED)}
    assert nodes[3].name == "C"
    assert nodes[3].type == int
    assert nodes[3].documentation == "dummy doc"
    assert nodes[3].input_types == {dummy.__name__: (Tuple[int, str, int], DependencyType.REQUIRED)}


def test_unpack_fields_valid_explicit_tuple_subset():
    def dummy() -> Tuple[int, str, int]:
        """dummy doc"""
        return 1, "2", 3

    annotation = function_modifiers.unpack_fields("A")
    annotation.validate(dummy)
    nodes = list(annotation.transform_node(node.Node.from_fn(dummy), {}, dummy))
    assert len(nodes) == 2

    assert nodes[0] == node.Node(
        name=dummy.__name__,
        typ=Tuple[int, str, int],
        doc_string=getattr(dummy, "__doc__", ""),
        callabl=dummy,
        tags={"module": "tests.function_modifiers.test_expanders"},
    )
    assert nodes[1].name == "A"
    assert nodes[1].type == int
    assert nodes[1].documentation == "dummy doc"
    assert nodes[1].input_types == {dummy.__name__: (Tuple[int, str, int], DependencyType.REQUIRED)}


def test_unpack_fields_valid_indeterminate_tuple():
    def dummy() -> Tuple[int, ...]:
        """dummy doc"""
        return 1, 2, 3

    annotation = function_modifiers.unpack_fields("A", "B", "C")
    annotation.validate(dummy)
    nodes = list(annotation.transform_node(node.Node.from_fn(dummy), {}, dummy))
    assert len(nodes) == 4

    assert nodes[0] == node.Node(
        name=dummy.__name__,
        typ=Tuple[int, ...],
        doc_string=getattr(dummy, "__doc__", ""),
        callabl=dummy,
        tags={"module": "tests.function_modifiers.test_expanders"},
    )
    assert nodes[1].name == "A"
    assert nodes[1].type == int
    assert nodes[1].documentation == "dummy doc"
    assert nodes[1].input_types == {dummy.__name__: (Tuple[int, ...], DependencyType.REQUIRED)}
    assert nodes[2].name == "B"
    assert nodes[2].type == int
    assert nodes[2].documentation == "dummy doc"
    assert nodes[2].input_types == {dummy.__name__: (Tuple[int, ...], DependencyType.REQUIRED)}
    assert nodes[3].name == "C"
    assert nodes[3].type == int
    assert nodes[3].documentation == "dummy doc"
    assert nodes[3].input_types == {dummy.__name__: (Tuple[int, ...], DependencyType.REQUIRED)}


@pytest.mark.parametrize(
    "return_type_str,fields",
    [
        ("Tuple[int, int]", ("A", "B")),
        ("Tuple[int, int, str]", ("A", "B", "C")),
        ("Tuple[int, ...]", ("A", "B")),
        pytest.param("tuple[int, int]", ("A", "B"), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[int, int, str]", ("A", "B", "C"), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[int, ...]", ("A", "B"), marks=skipif(**prior_to_py39)),
    ],
)
def test_unpack_fields_valid_type_annotations(return_type_str, fields):
    return_type = eval(return_type_str)

    def function() -> return_type:
        return 1, 2, "3"  # Only testing validation, so return value doesn't matter

    annotation = function_modifiers.unpack_fields(*fields)
    annotation.validate(function)


@pytest.mark.parametrize(
    "return_type_str,fields",
    [
        ("int", ("A",)),
        ("list", ("A",)),
        ("dict", ("A",)),
        ("Tuple", ("A",)),
        ("Tuple[int, int]", ("A", "B", "C")),
        pytest.param("Tuple[...]", ("A", "B", "C"), marks=skipif(**prior_to_py311)),
        pytest.param("Tuple[int, int, ...]", ("A", "B"), marks=skipif(**prior_to_py311)),
        pytest.param("Tuple[..., int, int]", ("A", "B"), marks=skipif(**prior_to_py311)),
        pytest.param("tuple", ("A",), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[int, int]", ("A", "B", "C"), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[...]", ("A", "B", "C"), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[int, int, ...]", ("A", "B"), marks=skipif(**prior_to_py39)),
        pytest.param("tuple[..., int, int]", ("A", "B"), marks=skipif(**prior_to_py39)),
    ],
)
def test_unpack_fields_invalid_type_annotations(return_type_str, fields):
    # NOTE: Prior to Python 3.11, improper use of the ellipsis in a typing.Tuple was an error.
    # However, improper use of an ellipsis in a (bare) tuple (python 3.9+) was not an error.

    return_type = eval(return_type_str)

    def function() -> return_type:
        return 1, 2, 3  # Only testing validation, so return value doesn't matter

    annotation = function_modifiers.unpack_fields(*fields)
    with pytest.raises(hamilton.function_modifiers.base.InvalidDecoratorException):
        annotation.validate(function)


def concat(upstream_parameter: str, literal_parameter: str) -> Any:
    """Concatenates {upstream_parameter} with literal_parameter"""
    return f"{upstream_parameter}{literal_parameter}"


def test_parametrized_full_no_replacement():
    annotation = function_modifiers.parameterize(replace_no_parameters={})
    (node_,) = annotation.expand_node(node.Node.from_fn(concat), {}, concat)
    assert node_.callable(upstream_parameter="foo", literal_parameter="bar") == "foobar"
    assert node_.input_types == {
        "literal_parameter": (str, DependencyType.REQUIRED),
        "upstream_parameter": (str, DependencyType.REQUIRED),
    }
    assert node_.documentation == concat.__doc__.format(upstream_parameter="upstream_parameter")


def test_parametrized_full_replace_just_upstream():
    annotation = function_modifiers.parameterize(
        replace_just_upstream_parameter={"upstream_parameter": source("foo_source")},
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(concat), {}, concat)
    assert node_.input_types == {
        "literal_parameter": (str, DependencyType.REQUIRED),
        "foo_source": (str, DependencyType.REQUIRED),
    }
    assert node_.callable(foo_source="foo", literal_parameter="bar") == "foobar"
    assert node_.documentation == concat.__doc__.format(upstream_parameter="foo_source")


def test_parametrized_full_replace_just_literal():
    annotation = function_modifiers.parameterize(
        replace_just_literal_parameter={"literal_parameter": value("bar")}
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(concat), {}, concat)
    assert node_.input_types == {"upstream_parameter": (str, DependencyType.REQUIRED)}
    assert node_.callable(upstream_parameter="foo") == "foobar"
    assert node_.documentation == concat.__doc__.format(upstream_parameter="upstream_parameter")


def test_parametrized_full_replace_both():
    annotation = function_modifiers.parameterize(
        replace_both_parameters={
            "upstream_parameter": source("foo_source"),
            "literal_parameter": value("bar"),
        }
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(concat), {}, concat)
    assert node_.input_types == {"foo_source": (str, DependencyType.REQUIRED)}
    assert node_.callable(foo_source="foo") == "foobar"
    assert node_.documentation == concat.__doc__.format(upstream_parameter="foo_source")


def test_parametrized_full_multiple_replacements():
    args = dict(
        replace_no_parameters=({}, "fn with no parameters replaced"),
        replace_just_upstream_parameter=(
            {"upstream_parameter": source("foo_source")},
            "fn with upstream_parameter set to node foo",
        ),
        replace_just_literal_parameter=(
            {"literal_parameter": value("bar")},
            "fn with upstream_parameter set to node foo",
        ),
        replace_both_parameters=(
            {"upstream_parameter": source("foo_source"), "literal_parameter": value("bar")},
            "fn with both parameters replaced",
        ),
    )
    annotation = function_modifiers.parameterize(**args)
    nodes = annotation.expand_node(node.Node.from_fn(concat), {}, concat)
    assert len(nodes) == 4
    # test out that documentation is assigned correctly
    assert [node_.documentation for node_ in nodes] == [args[node_.name][1] for node_ in nodes]


def test_parameterized_extract_columns():
    annotation = function_modifiers.parameterize_extract_columns(
        function_modifiers.ParameterizedExtract(
            ("outseries1a", "outseries2a"),
            {"input1": source("inseries1a"), "input2": source("inseries1b"), "input3": value(10)},
        ),
        function_modifiers.ParameterizedExtract(
            ("outseries1b", "outseries2b"),
            {"input1": source("inseries2a"), "input2": source("inseries2b"), "input3": value(100)},
        ),
    )

    def fn(input1: pd.Series, input2: pd.Series, input3: float) -> pd.DataFrame:
        return pd.concat([input1 * input2 * input3, input1 + input2 + input3], axis=1)

    nodes = annotation.expand_node(node.Node.from_fn(fn), {}, fn)
    # For each parameterized set, we have two outputs and the dataframe node
    assert len(nodes) == 6
    nodes_by_name = {node_.name: node_ for node_ in nodes}
    # Test that it produces the expected results
    pd.testing.assert_frame_equal(
        nodes_by_name["fn__0"](inseries1a=pd.Series([1]), inseries1b=pd.Series([1])),
        pd.DataFrame.from_dict({"outseries1a": [10], "outseries2a": [12]}),
    )
    pd.testing.assert_frame_equal(
        nodes_by_name["fn__1"](inseries2a=pd.Series([1]), inseries2b=pd.Series([1])),
        pd.DataFrame.from_dict({"outseries1b": [100], "outseries2b": [102]}),
    )
    # test that each of the "extractor" nodes produces exactly what we expect
    assert nodes_by_name["outseries1a"](fn__0=pd.DataFrame({"outseries1a": [10]}))[0] == 10
    assert nodes_by_name["outseries2a"](fn__0=pd.DataFrame({"outseries2a": [20]}))[0] == 20
    assert nodes_by_name["outseries1b"](fn__1=pd.DataFrame({"outseries1b": [30]}))[0] == 30
    assert nodes_by_name["outseries2b"](fn__1=pd.DataFrame({"outseries2b": [40]}))[0] == 40


def test_parametrized_full_replace_groups_with_literal():
    def add_n(grouped_parameter: List[int]) -> int:
        return sum(grouped_parameter)

    annotation = function_modifiers.parameterize(
        replace_just_literal_parameter={"grouped_parameter": group(value(1), value(2), value(3))}
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(add_n), {}, concat)
    assert node_.input_types == {}
    assert node_.callable() == 6


def test_parametrized_full_replace_groups_with_sources():
    def add_n(grouped_parameter: List[int]) -> int:
        return sum(grouped_parameter)

    annotation = function_modifiers.parameterize(
        replace_just_literal_parameter={
            "grouped_parameter": group(source("foo"), source("bar"), source("baz"))
        }
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(add_n), {}, concat)
    assert node_.input_types == {
        "foo": (int, DependencyType.REQUIRED),
        "bar": (int, DependencyType.REQUIRED),
        "baz": (int, DependencyType.REQUIRED),
    }
    assert node_.callable(foo=1, bar=2, baz=3) == 6


def test_parameterized_validate_group():
    def add_n(grouped_parameter: List[int]) -> int:
        return sum(grouped_parameter)

    annotation = function_modifiers.parameterize(
        replace_just_literal_parameter={
            "grouped_parameter": group(source("foo"), source("bar"), source("baz"))
        }
    )
    annotation.validate(add_n)


@pytest.mark.parametrize("annotation", [list, int, pd.Series, float])
def test_parameterized_validate_group_fails(annotation):
    def add_n(grouped_parameter: annotation) -> int:
        return sum(grouped_parameter)

    annotation = function_modifiers.parameterize(
        replace_just_literal_parameter={
            "grouped_parameter": group(source("foo"), source("bar"), source("baz"))
        }
    )
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(add_n)


def test_inject_list():
    annotation = function_modifiers.inject(nums=group(value(1), value(2), value(3)))

    def summation(nums: List[int]) -> int:
        return sum(nums)

    (node_,) = annotation.expand_node(node.Node.from_fn(summation), {}, summation)
    assert node_() == 6


def test_inject_dict():
    annotation = function_modifiers.inject(nums=group(one=value(1), two=value(2), three=value(3)))

    def summation(nums: Dict[str, int]) -> int:
        return nums["one"] + nums["two"] + nums["three"]

    (node_,) = annotation.expand_node(node.Node.from_fn(summation), {}, summation)
    assert node_() == 6


def test_inject_list_source():
    annotation = function_modifiers.inject(
        nums=group(source("one_source"), source("two_source"), source("three_source"))
    )

    def summation(nums: List[int]) -> int:
        return sum(nums)

    (node_,) = annotation.expand_node(node.Node.from_fn(summation), {}, summation)
    assert node_(one_source=1, two_source=2, three_source=3) == 6


def test_inject_dict_source():
    annotation = function_modifiers.inject(
        nums=group(one=source("one_source"), two=source("two_source"), three=source("three_source"))
    )

    def summation(nums: Dict[str, int]) -> int:
        return nums["one"] + nums["two"] + nums["three"]

    (node_,) = annotation.expand_node(node.Node.from_fn(summation), {}, summation)
    assert node_(one_source=1, two_source=2, three_source=3) == 6


def test_inject_multiple_things():
    def contrived_function(
        int_list: List[int],
        int_dict: Dict[str, int],
        int_value_injected: int,
        int_value_not_injected: int,
    ) -> int:
        return sum(int_list) + sum(int_dict.values()) + int_value_injected + int_value_not_injected

    annotation = function_modifiers.inject(
        int_list=group(value(1), value(2), source("three_source")),
        int_dict=group(one=value(4), two=value(5), three=source("six_source")),
        int_value_injected=value(7),
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(contrived_function), {}, contrived_function)
    assert node_(int_value_not_injected=8, three_source=3, six_source=6) == 8 * (8 + 1) // 2


@pytest.mark.parametrize(
    "annotated_type,cls,expected",
    [
        (List[int], GroupedListDependency, int),
        (List[List[int]], GroupedListDependency, List[int]),
        (List[pd.Series], GroupedListDependency, pd.Series),
        (Dict[str, pd.Series], GroupedDictDependency, pd.Series),
        (Dict[str, List[int]], GroupedDictDependency, List[int]),
        (Dict[str, int], GroupedDictDependency, int),
        (Optional[Dict[str, int]], GroupedDictDependency, int),
        (Optional[List[int]], GroupedListDependency, int),
    ],
)
def test_resolve_dependency_type_happy(
    annotated_type: Type[Type], cls: Type[GroupedDependency], expected: Type[Type]
):
    assert cls.resolve_dependency_type(annotated_type, "test") == expected


@pytest.mark.parametrize(
    "annotated_type,cls",
    [
        (int, GroupedDictDependency),
        (int, GroupedListDependency),
        (List[int], GroupedDictDependency),
        (Dict[str, int], GroupedListDependency),
        (pd.Series, GroupedDictDependency),
        (pd.Series, GroupedListDependency),
        (pd.DataFrame, GroupedDictDependency),
        (pd.DataFrame, GroupedListDependency),
        (Dict[int, str], GroupedDictDependency),
    ],
)
def test_resolve_dependency_type_sad(annotated_type: Type[Type], cls: Type[GroupedDependency]):
    with pytest.raises(base.InvalidDecoratorException):
        cls.resolve_dependency_type(annotated_type, "test")


def test_inject_misconfigured_param_type_list():
    def foo(x: int) -> int:
        return x

    annotation = function_modifiers.inject(x=group(value(1), value(2)))
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(foo)


def test_inject_misconfigured_param_type_dict():
    def foo(x: int) -> int:
        return x

    annotation = function_modifiers.inject(x=group(foo=value(1), bar=value(2)))
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(foo)


@pytest.mark.skipif(**prior_to_py39)
def test_inject_misconfigured_param_untyped_generic_list():
    # NOTE: Stricter typing rules for generics were introduced in Python 3.9.
    def foo(x: List) -> int:
        return sum(x)

    annotation = function_modifiers.inject(x=group(value(1), value(2)))
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(foo)


def test_inject_misconfigured_param_untyped_generic_dict():
    def foo(x: Dict) -> int:
        return sum(x)

    annotation = function_modifiers.inject(x=group(a=value(1), b=value(2)))
    with pytest.raises(base.InvalidDecoratorException):
        annotation.validate(foo)


def test_inject_validate_with_docstring():
    def foo(x: int) -> int:
        """Docstring..."""
        return x

    annotation = function_modifiers.inject(x=value(1))
    annotation.validate(foo)
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_.documentation == "Docstring..."


def test_inject_validate_with_docstring_replacement():
    def foo(x: int) -> int:
        """Docstring. x={x} is injected."""
        return x

    annotation = function_modifiers.inject(x=value(1))
    annotation.validate(foo)
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_.documentation == "Docstring. x=1 is injected."


def test_parameterize_repeated_sources():
    def foo(x: int, y: int) -> int:
        return x + y

    annotation = function_modifiers.parameterize(
        foo=dict(x=source("x"), y=source("x")),
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_(x=1) == 2


def test_parameterize_repeated_sources_with_group():
    def foo(x: List[int]) -> int:
        return sum(x)

    annotation = function_modifiers.parameterize(
        foo=dict(x=group(source("x"), source("x"))),
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_(x=1) == 2


def test_parameterize_with_parallelizable():
    def foo(n: int) -> Parallelizable[int]:
        for i in range(n):
            yield i

    annotation = function_modifiers.parameterize(
        foo=dict(x=source("x"), y=source("x")),
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_.node_role == node.NodeType.EXPAND


def test_parameterize_with_collect():
    def foo(n: Collect[int]) -> int:
        return sum(n)

    annotation = function_modifiers.parameterize(
        foo=dict(x=source("x"), y=source("x")),
    )
    (node_,) = annotation.expand_node(node.Node.from_fn(foo), {}, foo)
    assert node_.node_role == node.NodeType.COLLECT
