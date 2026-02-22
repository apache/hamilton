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

"""Tests for the Hamilton MCP server plugin.

These tests call the tool functions directly (no MCP client needed).
"""

from __future__ import annotations

import sys
import textwrap

import pytest

# Skip entire module if fastmcp is not available (optional dependency)
pytest.importorskip("fastmcp")

from hamilton.plugins.h_mcp import server as mcp_server
from hamilton.plugins.h_mcp._helpers import (
    build_driver_from_code,
    cleanup_temp_module,
    format_validation_errors,
    serialize_results,
)

# In FastMCP v3, @mcp.tool() returns the original function unchanged,
# so we can call the tool functions directly.
hamilton_validate_dag = mcp_server.hamilton_validate_dag
hamilton_list_nodes = mcp_server.hamilton_list_nodes
hamilton_get_docs = mcp_server.hamilton_get_docs
hamilton_scaffold = mcp_server.hamilton_scaffold

VALID_CODE = textwrap.dedent("""\
    import pandas as pd

    def spend(spend_raw: pd.Series) -> pd.Series:
        \"\"\"Clean spend data.\"\"\"
        return spend_raw.abs()

    def avg_spend(spend: pd.Series) -> pd.Series:
        \"\"\"Rolling average.\"\"\"
        return spend.rolling(3).mean()
""")

INVALID_CODE_SYNTAX = "def foo( -> int: return 1"

SIMPLE_CODE = textwrap.dedent("""\
    def a(a_input: int) -> int:
        return a_input + 1

    def b(a: int) -> int:
        return a * 2
""")


class TestValidateDag:
    def test_valid_code(self):
        result = hamilton_validate_dag(VALID_CODE)
        assert result["valid"] is True
        assert result["node_count"] > 0
        assert "spend" in result["nodes"]
        assert "avg_spend" in result["nodes"]
        assert "spend_raw" in result["inputs"]
        assert result["errors"] == []

    def test_syntax_error(self):
        result = hamilton_validate_dag(INVALID_CODE_SYNTAX)
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert result["errors"][0]["type"] == "SyntaxError"
        assert result["node_count"] == 0

    def test_simple_code(self):
        result = hamilton_validate_dag(SIMPLE_CODE)
        assert result["valid"] is True
        assert "a" in result["nodes"]
        assert "b" in result["nodes"]
        assert "a_input" in result["inputs"]


class TestListNodes:
    def test_basic(self):
        result = hamilton_list_nodes(VALID_CODE)
        assert result["errors"] == []
        names = [n["name"] for n in result["nodes"]]
        assert "spend" in names
        assert "avg_spend" in names

    def test_node_details(self):
        result = hamilton_list_nodes(SIMPLE_CODE)
        assert result["errors"] == []
        node_map = {n["name"]: n for n in result["nodes"]}
        assert "a" in node_map
        assert node_map["a"]["is_external_input"] is False
        assert "a_input" in node_map["a"]["required_dependencies"]

    def test_syntax_error(self):
        result = hamilton_list_nodes(INVALID_CODE_SYNTAX)
        assert result["nodes"] == []
        assert len(result["errors"]) > 0


class TestGetDocs:
    def test_overview(self):
        result = hamilton_get_docs("overview")
        assert len(result) > 0
        assert "Hamilton" in result
        assert "DAG" in result

    def test_decorators_list(self):
        result = hamilton_get_docs("decorators")
        assert "parameterize" in result
        assert "extract_columns" in result

    def test_specific_decorator(self):
        result = hamilton_get_docs("parameterize")
        assert len(result) > 0
        assert "parameterize" in result.lower()

    def test_driver_topic(self):
        result = hamilton_get_docs("driver")
        assert len(result) > 0

    def test_unknown_topic(self):
        result = hamilton_get_docs("nonexistent_topic_xyz")
        assert "Unknown topic" in result


class TestScaffold:
    def test_basic_pattern(self):
        code = hamilton_scaffold("basic")
        assert "def raw_data" in code
        assert "def cleaned" in code
        # Validate the scaffold code compiles as a valid DAG
        result = hamilton_validate_dag(code)
        assert result["valid"] is True

    def test_parameterized_pattern(self):
        code = hamilton_scaffold("parameterized")
        assert "parameterize" in code
        assert "rolling_mean" in code

    def test_config_based_pattern(self):
        code = hamilton_scaffold("config_based")
        assert "config.when" in code

    def test_data_pipeline_pattern(self):
        code = hamilton_scaffold("data_pipeline")
        assert "def raw_data" in code
        result = hamilton_validate_dag(code)
        assert result["valid"] is True

    def test_ml_pipeline_pattern(self):
        code = hamilton_scaffold("ml_pipeline")
        assert "feature_matrix" in code
        result = hamilton_validate_dag(code)
        assert result["valid"] is True

    def test_data_quality_pattern(self):
        code = hamilton_scaffold("data_quality")
        assert "check_output" in code

    def test_unknown_pattern(self):
        result = hamilton_scaffold("nonexistent")
        assert "Unknown pattern" in result

    def test_all_patterns_valid(self):
        """Every scaffold pattern should produce code that validates."""
        for pattern in ["basic", "data_pipeline", "ml_pipeline"]:
            code = hamilton_scaffold(pattern)
            result = hamilton_validate_dag(code)
            assert result["valid"] is True, f"Pattern '{pattern}' did not validate: {result}"


class TestHelpers:
    def test_build_and_cleanup(self):
        dr, module = build_driver_from_code(SIMPLE_CODE)
        module_name = module.__name__
        assert module_name in sys.modules
        cleanup_temp_module(module)
        assert module_name not in sys.modules

    def test_format_validation_errors_syntax(self):
        try:
            compile("def foo( -> int:", "<test>", "exec")
        except SyntaxError as exc:
            errors = format_validation_errors(exc)
            assert len(errors) == 1
            assert errors[0]["type"] == "SyntaxError"

    def test_format_validation_errors_value(self):
        exc = ValueError("something went wrong")
        errors = format_validation_errors(exc)
        assert errors[0]["type"] == "ValueError"
        assert "something went wrong" in errors[0]["message"]

    def test_serialize_results_basic(self):
        results = {"count": 42, "name": "test"}
        serialized = serialize_results(results)
        assert serialized["count"] == "42"
        assert serialized["name"] == "test"

    def test_serialize_results_pandas(self):
        import pandas as pd

        results = {"series": pd.Series([1, 2, 3]), "df": pd.DataFrame({"a": [1]})}
        serialized = serialize_results(results)
        assert isinstance(serialized["series"], dict)
        assert isinstance(serialized["df"], dict)
