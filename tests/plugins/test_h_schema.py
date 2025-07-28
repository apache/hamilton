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

import json
import pathlib

import pandas as pd
import pyarrow
import pytest

from hamilton import graph_types
from hamilton.plugins import h_schema


@pytest.fixture
def schema1():
    yield pyarrow.schema(
        [
            ("foo", pyarrow.string()),
            ("bar", pyarrow.int64()),
        ]
    )


@pytest.fixture
def schema2():
    yield pyarrow.schema(
        [
            ("foo", pyarrow.string()),
            ("bar", pyarrow.int64()),
            ("baz", pyarrow.bool_()),
        ]
    )


@pytest.fixture
def schema3():
    yield pyarrow.schema(
        [
            ("foo", pyarrow.string()),
            ("bar", pyarrow.float64()),
        ]
    )


@pytest.fixture
def metadata1():
    yield {"key": "value1"}


@pytest.fixture
def metadata2():
    yield {"key": "value2"}


def test_schema_no_diff(schema1: pyarrow.Schema):
    diff = h_schema.diff_schemas(schema1, schema1)
    assert diff == {}

    human_readable_diff = h_schema.human_readable_diff(diff)
    assert human_readable_diff == {}


def test_schema_added_node(schema1: pyarrow.Schema, schema2: pyarrow.Schema):
    schema_diff = h_schema.diff_schemas(schema2, schema1)
    assert schema_diff["baz"].diff == h_schema.Diff.ADDED

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"baz": "+"}


def test_schema_removed_node(schema1: pyarrow.Schema, schema2: pyarrow.Schema):
    schema_diff = h_schema.diff_schemas(schema1, schema2)
    assert schema_diff["baz"].diff == h_schema.Diff.REMOVED

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"baz": "-"}


def test_schema_edited_node(schema1: pyarrow.Schema, schema3: pyarrow.Schema):
    schema_diff = h_schema.diff_schemas(schema1, schema3)
    assert schema_diff["bar"].diff == h_schema.Diff.UNEQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"bar": {"type": {"cur": "int64", "ref": "double"}}}


def test_schema_equal_no_schema_metadata_diff(schema1: pyarrow.Schema):
    metadata = {"key": "value"}
    schema1 = schema1.with_metadata(metadata)
    schema_diff = h_schema.diff_schemas(schema1, schema1, check_schema_metadata=True)
    assert schema_diff == {}

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {}


def test_schema_unequal_but_no_schema_metadata_diff(
    schema1: pyarrow.Schema,
    schema2: pyarrow.Schema,
    metadata1: dict,
):
    schema1 = schema1.with_metadata(metadata1)
    schema2 = schema2.with_metadata(metadata1)

    schema_diff = h_schema.diff_schemas(schema1, schema2, check_schema_metadata=True)

    assert schema_diff["baz"].diff == h_schema.Diff.REMOVED
    assert schema_diff[h_schema.SCHEMA_METADATA_FIELD].value["key"].diff == h_schema.Diff.EQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"baz": "-"}


def test_schema_added_schema_metadata(schema1: pyarrow.Schema, metadata1: dict):
    schema1_with_metadata = schema1.with_metadata(metadata1)

    schema_diff = h_schema.diff_schemas(schema1_with_metadata, schema1, check_schema_metadata=True)

    assert schema_diff[h_schema.SCHEMA_METADATA_FIELD].value["key"].diff == h_schema.Diff.ADDED

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {h_schema.SCHEMA_METADATA_FIELD: {"key": "+"}}


def test_schema_removed_schema_metadata(schema1: pyarrow.Schema, metadata1: dict):
    schema1_with_metadata = schema1.with_metadata(metadata1)

    schema_diff = h_schema.diff_schemas(schema1, schema1_with_metadata, check_schema_metadata=True)

    assert schema_diff[h_schema.SCHEMA_METADATA_FIELD].value["key"].diff == h_schema.Diff.REMOVED

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {h_schema.SCHEMA_METADATA_FIELD: {"key": "-"}}


def test_schema_edited_schema_metadata(schema1: pyarrow.Schema, metadata1: dict, metadata2: dict):
    schema1_with_metadata1 = schema1.with_metadata(metadata1)
    schema1_with_metadata2 = schema1.with_metadata(metadata2)

    schema_diff = h_schema.diff_schemas(
        schema1_with_metadata1, schema1_with_metadata2, check_schema_metadata=True
    )

    assert schema_diff[h_schema.SCHEMA_METADATA_FIELD].value["key"].diff == h_schema.Diff.UNEQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)

    assert human_readable_diff == {
        h_schema.SCHEMA_METADATA_FIELD: {"key": {"cur": "value1", "ref": "value2"}}
    }


def test_schema_added_field_metadata(schema1: pyarrow.Schema, metadata1: dict):
    field0 = schema1.field(0)
    schema1_with_field_metadata = pyarrow.schema(
        [field0.with_metadata(metadata1), schema1.field(1)]
    )

    schema_diff = h_schema.diff_schemas(
        schema1_with_field_metadata, schema1, check_field_metadata=True
    )

    assert schema_diff[field0.name].diff == h_schema.Diff.UNEQUAL
    assert schema_diff[field0.name].value["metadata"].diff == h_schema.Diff.UNEQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"foo": {"metadata": {"key": "+"}}}


def test_schema_removed_field_metadata(schema1: pyarrow.Schema, metadata1: dict):
    field0 = schema1.field(0)
    schema1_with_field_metadata = pyarrow.schema(
        [field0.with_metadata(metadata1), schema1.field(1)]
    )

    schema_diff = h_schema.diff_schemas(
        schema1, schema1_with_field_metadata, check_field_metadata=True
    )

    assert schema_diff[field0.name].diff == h_schema.Diff.UNEQUAL
    assert schema_diff[field0.name].value["metadata"].diff == h_schema.Diff.UNEQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"foo": {"metadata": {"key": "-"}}}


def test_schema_edited_field_metadata(schema1: pyarrow.Schema, metadata1: dict, metadata2: dict):
    field0 = schema1.field(0)
    schema1_with_field_metadata1 = pyarrow.schema(
        [field0.with_metadata(metadata1), schema1.field(1)]
    )
    schema1_with_field_metadata2 = pyarrow.schema(
        [field0.with_metadata(metadata2), schema1.field(1)]
    )

    schema_diff = h_schema.diff_schemas(
        schema1_with_field_metadata1, schema1_with_field_metadata2, check_field_metadata=True
    )

    assert schema_diff[field0.name].diff == h_schema.Diff.UNEQUAL
    assert schema_diff[field0.name].value["metadata"].diff == h_schema.Diff.UNEQUAL

    human_readable_diff = h_schema.human_readable_diff(schema_diff)
    assert human_readable_diff == {"foo": {"metadata": {"key": {"cur": "value1", "ref": "value2"}}}}


def test_pyarrow_schema_equals_json_schema(schema1: pyarrow.Schema, metadata1: dict):
    schema1_with_metadata1 = schema1.with_metadata(metadata1)
    expected_json = {
        h_schema.SCHEMA_METADATA_FIELD: {"key": "value1"},
        "foo": {"name": "foo", "type": "string", "nullable": True, "metadata": {}},
        "bar": {"name": "bar", "type": "int64", "nullable": True, "metadata": {}},
    }

    schema_json = h_schema.pyarrow_schema_to_json(schema1_with_metadata1)
    assert expected_json == schema_json
    # ensure the returned schema is JSON-serializable
    assert json.dumps(expected_json) == json.dumps(schema_json)


def test_load_schema_from_disk(schema1: pyarrow.Schema, tmp_path: pathlib.Path):
    schema_path = tmp_path / "my_schema.schema"
    pathlib.Path(schema_path).write_bytes(schema1.serialize())
    loaded_schema = h_schema.load_schema(schema_path)
    assert schema1.equals(loaded_schema)


def test_save_schema_to_disk(schema1: pyarrow.Schema, tmp_path: pathlib.Path):
    schema_path = tmp_path / "my_schema.schema"
    h_schema.save_schema(path=schema_path, schema=schema1)
    loaded_schema = pyarrow.ipc.read_schema(schema_path)
    assert schema1.equals(loaded_schema)


def test_get_dataframe_schema():
    def foo(x: pd.DataFrame) -> pd.DataFrame:
        """doc"""
        return x

    version = graph_types.hash_source_code(foo, strip=True)
    node = graph_types.HamiltonNode(
        name=foo.__name__,
        type=pd.DataFrame,
        documentation=foo.__doc__,
        tags={},
        is_external_input=False,
        originating_functions=(foo,),
        required_dependencies=set(),
        optional_dependencies=set(),
        optional_dependencies_default_values={},
    )
    df = pd.DataFrame({"a": [0, 1], "b": [True, False]})

    expected_schema = pyarrow.schema(
        [
            ("a", "int64"),
            ("b", "bool"),
        ]
    )
    expected_metadata = {
        b"name": foo.__name__.encode(),
        b"documentation": foo.__doc__.encode(),
        b"version": version.encode(),
    }

    schema = h_schema.get_dataframe_schema(df, node)

    assert schema.equals(expected_schema.with_metadata(expected_metadata), check_metadata=True)


def test_schema_validator_after_node_execution(tmp_path):
    def foo(x: pd.DataFrame) -> pd.DataFrame:
        """doc"""
        return x

    version = graph_types.hash_source_code(foo, strip=True)
    node = graph_types.HamiltonNode(
        name=foo.__name__,
        type=pd.DataFrame,
        documentation=foo.__doc__,
        tags={},
        is_external_input=False,
        originating_functions=(foo,),
        required_dependencies=set(),
        optional_dependencies=set(),
        optional_dependencies_default_values={},
    )
    h_graph = graph_types.HamiltonGraph([node])
    df = pd.DataFrame({"a": [0, 1], "b": [True, False]})

    expected_schema = pyarrow.schema(
        [
            ("a", "int64"),
            ("b", "bool"),
        ]
    )
    expected_metadata = {
        b"name": foo.__name__.encode(),
        b"documentation": foo.__doc__.encode(),
        b"version": version.encode(),
    }

    # set the HamiltonGraph on the state of the adaper
    adapter = h_schema.SchemaValidator(schema_dir=tmp_path)
    adapter.h_graph = h_graph

    adapter.run_after_node_execution(node_name=foo.__name__, result=df)

    tracked_schema = adapter.schemas[foo.__name__]
    assert tracked_schema.equals(
        expected_schema.with_metadata(expected_metadata), check_metadata=True
    )
