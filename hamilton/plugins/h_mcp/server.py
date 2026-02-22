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

from __future__ import annotations

import inspect
import textwrap
import threading
import time

from fastmcp import FastMCP

from hamilton.plugins.h_mcp._helpers import (
    build_driver_from_code,
    cleanup_temp_module,
    format_exception_chain,
    serialize_results,
)

mcp = FastMCP(
    name="Hamilton",
    instructions=(
        "Hamilton is a Python micro-framework where functions define DAG nodes. "
        "Use hamilton_validate_dag to check code before execution. "
        "Workflow: scaffold -> validate -> visualize -> correct -> execute."
    ),
)


@mcp.tool()
def hamilton_validate_dag(code: str, config: dict | None = None) -> dict:
    """Validate Hamilton DAG code by building the Driver.

    Compiles Python source into a Hamilton DAG and checks for missing
    dependencies, type mismatches, and circular references -- all without
    executing the code.

    Returns ``{"valid": true, "node_count": N, "nodes": [...], "inputs": [...]}``
    on success or ``{"valid": false, "errors": [...]}`` on failure.
    """
    module = None
    try:
        dr, module = build_driver_from_code(code, config)
        variables = dr.list_available_variables()
        nodes = [v.name for v in variables if not v.is_external_input]
        inputs = [v.name for v in variables if v.is_external_input]
        return {
            "valid": True,
            "node_count": len(nodes),
            "nodes": sorted(nodes),
            "inputs": sorted(inputs),
            "errors": [],
        }
    except Exception as exc:
        return {
            "valid": False,
            "node_count": 0,
            "nodes": [],
            "inputs": [],
            "errors": format_exception_chain(exc),
        }
    finally:
        if module is not None:
            cleanup_temp_module(module)


@mcp.tool()
def hamilton_list_nodes(code: str, config: dict | None = None) -> dict:
    """List all nodes in a Hamilton DAG with their types and dependencies.

    Builds the DAG from source, then returns structured info for every node
    including name, output type, tags, whether it is an external input,
    and its required/optional dependencies.
    """
    module = None
    try:
        dr, module = build_driver_from_code(code, config)
        variables = dr.list_available_variables()
        from hamilton.htypes import get_type_as_string

        node_list = []
        for v in variables:
            node_list.append(
                {
                    "name": v.name,
                    "type": get_type_as_string(v.type) or "",
                    "is_external_input": v.is_external_input,
                    "tags": v.tags,
                    "required_dependencies": sorted(v.required_dependencies),
                    "optional_dependencies": sorted(v.optional_dependencies),
                    "documentation": v.documentation,
                }
            )
        return {"nodes": node_list, "errors": []}
    except Exception as exc:
        return {"nodes": [], "errors": format_exception_chain(exc)}
    finally:
        if module is not None:
            cleanup_temp_module(module)


@mcp.tool()
def hamilton_visualize(code: str, config: dict | None = None, output_format: str = "dot") -> str:
    """Visualize the Hamilton DAG as DOT graph source.

    Builds the DAG and returns a Graphviz DOT-language string describing
    the dependency graph. Requires ``graphviz`` (``pip install "apache-hamilton[visualization]"``).
    """
    module = None
    try:
        dr, module = build_driver_from_code(code, config)
        try:
            dot = dr.display_all_functions(render_kwargs={"view": False})
        except ImportError:
            return (
                "Error: graphviz is required for visualization. "
                'Install with: pip install "apache-hamilton[visualization]"'
            )
        if dot is None:
            return (
                "Error: graphviz is required for visualization. "
                'Install with: pip install "apache-hamilton[visualization]"'
            )
        return dot.source
    except Exception as exc:
        return f"Error: {exc}"
    finally:
        if module is not None:
            cleanup_temp_module(module)


@mcp.tool()
def hamilton_execute(
    code: str,
    final_vars: list[str],
    inputs: dict | None = None,
    config: dict | None = None,
    timeout_seconds: int = 30,
) -> dict:
    """Execute a Hamilton DAG and return the requested outputs.

    Builds the DAG from source, then calls ``driver.execute()`` with the
    given ``final_vars`` and ``inputs``. Results are serialized to JSON-safe
    strings. A timeout (default 30s) guards against long-running code.

    WARNING: This executes arbitrary Python code.
    """
    module = None
    result_container: dict = {}
    error_container: dict = {}

    def _run(dr, final_vars, inputs):
        try:
            result_container["results"] = dr.execute(final_vars=final_vars, inputs=inputs or {})
        except Exception as exc:
            error_container["error"] = exc

    try:
        dr, module = build_driver_from_code(code, config)

        start = time.monotonic()
        worker = threading.Thread(target=_run, args=(dr, final_vars, inputs))
        worker.start()
        worker.join(timeout=timeout_seconds)

        if worker.is_alive():
            return {"error": f"Execution timed out after {timeout_seconds}s"}

        elapsed_ms = round((time.monotonic() - start) * 1000, 1)

        if "error" in error_container:
            return {
                "error": str(error_container["error"]),
                "execution_time_ms": elapsed_ms,
            }

        return {
            "results": serialize_results(result_container["results"]),
            "execution_time_ms": elapsed_ms,
        }
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        if module is not None:
            cleanup_temp_module(module)


@mcp.tool()
def hamilton_get_docs(topic: str) -> str:
    """Get Hamilton documentation for a specific topic.

    Supported topics: ``overview``, ``decorators``, ``driver``, ``builder``,
    or any decorator name such as ``parameterize``, ``extract_columns``,
    ``config``, ``check_output``, ``tag``, ``pipe``, ``does``, ``subdag``, etc.
    """
    topic = topic.strip().lower()

    if topic == "overview":
        return textwrap.dedent("""\
            Hamilton -- Python micro-framework for dataflow DAGs

            Core concepts:
            - Each Python function defines a DAG node.
            - The function name becomes the node name.
            - Function parameters declare dependencies on other nodes.
            - Return type annotations are required.
            - The Driver compiles functions into a DAG, validates dependencies
              and types at build time, then executes the graph.

            Quick start:
              1. Write functions in a module (my_functions.py).
              2. Build a Driver:
                   from hamilton import driver
                   import my_functions
                   dr = driver.Builder().with_modules(my_functions).build()
              3. Execute:
                   results = dr.execute(["output_node"], inputs={...})

            Key decorators: @parameterize, @extract_columns, @config.when,
            @check_output, @tag, @pipe, @does, @subdag
        """)

    if topic == "decorators":
        from hamilton import function_modifiers

        decorators = {
            "parameterize": "Create multiple nodes from one function with different parameters.",
            "parameterize_sources": "Parameterize by mapping different source nodes.",
            "parameterize_values": "Parameterize by mapping different literal values.",
            "extract_columns": "Expand a DataFrame-returning function into per-column nodes.",
            "extract_fields": "Expand a dict-returning function into per-field nodes.",
            "config.when": "Conditionally include a function based on config values.",
            "check_output": "Attach data quality validators to a node's output.",
            "tag": "Add metadata tags to a node.",
            "tag_outputs": "Tag specific outputs of a multi-output function.",
            "pipe": "Chain transforms: pass a node's output through a pipeline.",
            "does": "Replace function body with another callable.",
            "subdag": "Include an entire sub-DAG as a namespace.",
            "inject": "Inject specific values or sources into function parameters.",
            "schema": "Attach schema metadata to a node.",
            "cache": "Mark a node for caching.",
            "load_from": "Load data from an external source (data loader).",
            "save_to": "Save data to an external destination (data saver).",
        }
        lines = ["Available Hamilton decorators:\n"]
        for name, desc in decorators.items():
            lines.append(f"  @{name} -- {desc}")
        lines.append("\nUse hamilton_get_docs('<decorator_name>') for full documentation.")
        return "\n".join(lines)

    if topic in ("driver", "builder"):
        from hamilton import driver as driver_mod

        doc = inspect.getdoc(driver_mod.Builder)
        return doc or "No documentation found for Builder."

    # Try to find a decorator by name in function_modifiers
    from hamilton import function_modifiers

    obj = getattr(function_modifiers, topic, None)
    if obj is not None:
        doc = inspect.getdoc(obj)
        if doc:
            return f"@{topic}\n\n{doc}"
        # For class-based decorators, try the class itself
        if isinstance(obj, type):
            doc = inspect.getdoc(obj)
            if doc:
                return f"@{topic}\n\n{doc}"

    return (
        f"Unknown topic '{topic}'. "
        "Supported: overview, decorators, driver, builder, "
        "or any decorator name (parameterize, extract_columns, config, "
        "check_output, tag, pipe, does, subdag, etc.)"
    )


@mcp.tool()
def hamilton_scaffold(pattern: str) -> str:
    """Generate a starter Hamilton module for a given pattern.

    Supported patterns: ``basic``, ``parameterized``, ``config_based``,
    ``data_pipeline``, ``ml_pipeline``, ``data_quality``.

    Returns Python source code that is a valid Hamilton module, plus a
    driver script example.
    """
    templates = {
        "basic": textwrap.dedent('''\
            """Basic Hamilton module example."""
            import pandas as pd


            def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
                """Pass-through for raw input data."""
                return raw_data_input


            def cleaned(raw_data: pd.DataFrame) -> pd.DataFrame:
                """Drop rows with missing values."""
                return raw_data.dropna()


            def row_count(cleaned: pd.DataFrame) -> int:
                """Count rows after cleaning."""
                return len(cleaned)


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["row_count", "cleaned"],
            #     inputs={"raw_data_input": pd.DataFrame({"a": [1, 2, None], "b": [4, None, 6]})},
            # )
            # print(result)
        '''),
        "parameterized": textwrap.dedent('''\
            """Hamilton module using @parameterize to create multiple nodes."""
            import pandas as pd

            from hamilton.function_modifiers import parameterize, value


            @parameterize(
                weekly_mean={"window": value(7)},
                monthly_mean={"window": value(30)},
            )
            def rolling_mean(time_series: pd.Series, window: int) -> pd.Series:
                """Compute a rolling mean with a given window size."""
                return time_series.rolling(window).mean()


            def time_series(time_series_input: pd.Series) -> pd.Series:
                """Pass-through for time series input."""
                return time_series_input


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["weekly_mean", "monthly_mean"],
            #     inputs={"time_series_input": pd.Series(range(60))},
            # )
        '''),
        "config_based": textwrap.dedent('''\
            """Hamilton module using @config.when for conditional logic."""
            import pandas as pd

            from hamilton.function_modifiers import config


            @config.when(env="production")
            def data_source__prod(db_connection_string: str) -> pd.DataFrame:
                """Load data from production database."""
                # In real code: pd.read_sql("SELECT * FROM table", db_connection_string)
                return pd.DataFrame({"value": [1, 2, 3]})


            @config.when(env="development")
            def data_source__dev() -> pd.DataFrame:
                """Return sample data for development."""
                return pd.DataFrame({"value": [10, 20, 30]})


            def processed(data_source: pd.DataFrame) -> pd.DataFrame:
                """Process the data source."""
                return data_source.assign(doubled=data_source["value"] * 2)


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = (
            #     driver.Builder()
            #     .with_modules(my_module)
            #     .with_config({"env": "development"})
            #     .build()
            # )
            # result = dr.execute(["processed"])
        '''),
        "data_pipeline": textwrap.dedent('''\
            """Hamilton data pipeline: ingest -> clean -> transform -> aggregate."""
            import pandas as pd


            def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
                """Ingest raw data."""
                return raw_data_input


            def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
                """Remove nulls and duplicates."""
                return raw_data.dropna().drop_duplicates()


            def spend(cleaned_data: pd.DataFrame) -> pd.Series:
                """Extract the spend column."""
                return cleaned_data["spend"].abs()


            def avg_spend(spend: pd.Series) -> float:
                """Average spend across all records."""
                return spend.mean()


            def total_spend(spend: pd.Series) -> float:
                """Total spend across all records."""
                return spend.sum()


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["avg_spend", "total_spend"],
            #     inputs={"raw_data_input": pd.DataFrame({"spend": [-10, 20, -30]})},
            # )
        '''),
        "ml_pipeline": textwrap.dedent('''\
            """Hamilton ML pipeline: features -> train/test split -> model -> metrics."""
            import pandas as pd
            import numpy as np


            def feature_matrix(feature_matrix_input: pd.DataFrame) -> pd.DataFrame:
                """Input feature matrix."""
                return feature_matrix_input


            def target(target_input: pd.Series) -> pd.Series:
                """Input target variable."""
                return target_input


            def train_fraction() -> float:
                """Fraction of data for training."""
                return 0.8


            def train_indices(
                feature_matrix: pd.DataFrame, train_fraction: float
            ) -> np.ndarray:
                """Random train indices."""
                n = len(feature_matrix)
                idx = np.arange(n)
                np.random.shuffle(idx)
                return idx[: int(n * train_fraction)]


            def test_indices(
                feature_matrix: pd.DataFrame, train_indices: np.ndarray
            ) -> np.ndarray:
                """Test indices (complement of train)."""
                all_idx = set(range(len(feature_matrix)))
                return np.array(sorted(all_idx - set(train_indices)))


            def train_X(feature_matrix: pd.DataFrame, train_indices: np.ndarray) -> pd.DataFrame:
                """Training features."""
                return feature_matrix.iloc[train_indices]


            def test_X(feature_matrix: pd.DataFrame, test_indices: np.ndarray) -> pd.DataFrame:
                """Test features."""
                return feature_matrix.iloc[test_indices]


            def train_y(target: pd.Series, train_indices: np.ndarray) -> pd.Series:
                """Training target."""
                return target.iloc[train_indices]


            def test_y(target: pd.Series, test_indices: np.ndarray) -> pd.Series:
                """Test target."""
                return target.iloc[test_indices]


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["train_X", "test_X", "train_y", "test_y"],
            #     inputs={
            #         "feature_matrix_input": pd.DataFrame({"a": range(100), "b": range(100)}),
            #         "target_input": pd.Series(range(100)),
            #     },
            # )
        '''),
        "data_quality": textwrap.dedent('''\
            """Hamilton module with data quality checks using @check_output."""
            import pandas as pd
            import numpy as np

            from hamilton.function_modifiers import check_output


            @check_output(
                data_type=np.float64,
                range=(0, None),
            )
            def spend(spend_raw: pd.Series) -> pd.Series:
                """Clean spend: ensure non-negative floats."""
                return spend_raw.abs().astype(float)


            @check_output(
                data_type=np.float64,
            )
            def revenue(revenue_raw: pd.Series) -> pd.Series:
                """Clean revenue data."""
                return revenue_raw.astype(float)


            def profit(revenue: pd.Series, spend: pd.Series) -> pd.Series:
                """Profit = revenue - spend."""
                return revenue - spend


            # --- Driver script ---
            # from hamilton import driver
            # import my_module
            #
            # dr = driver.Builder().with_modules(my_module).build()
            # result = dr.execute(
            #     ["profit"],
            #     inputs={
            #         "spend_raw": pd.Series([10, 20, 30]),
            #         "revenue_raw": pd.Series([100, 200, 300]),
            #     },
            # )
        '''),
    }

    pattern = pattern.strip().lower()
    template = templates.get(pattern)
    if template is None:
        available = ", ".join(sorted(templates.keys()))
        return f"Unknown pattern '{pattern}'. Available patterns: {available}"

    return template
