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
from hamilton.plugins.h_mcp._templates import get_available_templates, get_capabilities

mcp = FastMCP(
    name="Hamilton",
    instructions=(
        "Hamilton is a Python micro-framework where functions define DAG nodes. "
        "Ask the user which data libraries they use (e.g., pandas, numpy, polars) "
        "then call hamilton_capabilities with their preferred_libraries. "
        "Use hamilton_validate_dag to check code before execution. "
        "Workflow: ask user -> capabilities -> scaffold -> validate -> visualize -> correct -> execute."
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
def hamilton_capabilities(preferred_libraries: list[str] | None = None) -> dict:
    """Report which optional libraries are installed and which features are available.

    Call this first to discover the environment before generating code.
    If the user specifies which libraries they use, pass them as
    ``preferred_libraries`` (e.g., ``["pandas", "numpy"]``) to filter
    scaffold patterns accordingly.
    """
    prefs = set(preferred_libraries) if preferred_libraries is not None else None
    return get_capabilities(prefs)


@mcp.tool()
def hamilton_scaffold(
    pattern: str,
    preferred_libraries: list[str] | None = None,
) -> str:
    """Generate a starter Hamilton module for a given pattern.

    Available patterns depend on installed or preferred libraries.
    Pass ``preferred_libraries`` to filter to patterns matching the
    user's environment (e.g., ``["pandas"]``).
    """
    prefs = set(preferred_libraries) if preferred_libraries is not None else None
    templates = get_available_templates(prefs)
    pattern = pattern.strip().lower()
    template = templates.get(pattern)
    if template is None:
        available = ", ".join(sorted(templates.keys()))
        return f"Unknown pattern '{pattern}'. Available patterns: {available}"

    return template.code
