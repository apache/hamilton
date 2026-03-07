<!--
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.
-->

---
name: hamilton-mcp
description: Interactive Hamilton DAG development via MCP tools. Validate, visualize, scaffold, and execute Hamilton pipelines without leaving the conversation. Use when building or debugging Hamilton dataflows interactively.
allowed-tools: Read, Grep, Glob, Bash(hamilton-mcp:*), Bash(python:*), Bash(pip:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton MCP Server -- Interactive DAG Development

The Hamilton MCP server exposes Hamilton's DAG compilation, validation, and execution as interactive tools. It enables a tight feedback loop: write functions, validate the DAG, visualize dependencies, fix errors, and execute -- all without leaving the conversation.

## Setup

**Run via uvx (recommended).** Add `--with` for whichever libraries your code uses:
```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp                              # minimal
uvx --from "apache-hamilton[mcp]" --with pandas --with numpy hamilton-mcp   # pandas/numpy project
uvx --from "apache-hamilton[mcp]" --with polars hamilton-mcp                # polars project
```

**Or install and run directly:**
```bash
pip install "apache-hamilton[mcp]"
hamilton-mcp
```

**Or use programmatically:**
```python
from hamilton.plugins.h_mcp import get_mcp_server

mcp = get_mcp_server()
mcp.run()
```

## Workflow: The Golden Path

Always follow this sequence when building Hamilton DAGs interactively:

```
ask user -> capabilities -> scaffold -> validate -> visualize -> correct -> execute
```

### Step 1: Ask the User Which Libraries They Use

**Before calling any tool, ask the user which data libraries they use** (pandas, numpy, polars, etc.). Then pass their answer as `preferred_libraries` to `hamilton_capabilities` and `hamilton_scaffold`. This ensures scaffolds match the user's project, not the server's environment.

```json
// Example: user says "I use pandas"
// Tool call: hamilton_capabilities(preferred_libraries=["pandas"])
{
  "libraries": {
    "pandas": true,
    "numpy": true,
    "polars": false,
    "graphviz": true
  },
  "available_scaffolds": [
    "basic", "basic_pure_python", "config_based",
    "data_pipeline", "parameterized"
  ]
}
```

**Decision rules:**
- If user says pandas: use pandas-based scaffolds and DataFrame/Series types
- If user has no preference or only uses built-in types: use `basic_pure_python` scaffold and `int`/`float`/`str`/`dict` types
- If `graphviz` is available: use `hamilton_visualize` to show the DAG structure
- Never generate code that imports libraries the user hasn't stated they use

### Step 2: Scaffold a Starting Point

Use `hamilton_scaffold` with a pattern name from the capabilities response:

| Pattern | Libraries Required | Use Case |
|---------|-------------------|----------|
| `basic_pure_python` | None | Simple pipelines with built-in types |
| `basic` | pandas | DataFrame cleaning & counting |
| `parameterized` | pandas | Multiple nodes from one function |
| `config_based` | pandas | Environment-conditional logic |
| `data_pipeline` | pandas | ETL: ingest, clean, transform, aggregate |
| `ml_pipeline` | pandas, numpy | Feature engineering & train/test split |
| `data_quality` | pandas, numpy | Validation with `@check_output` |

### Step 3: Validate Before Executing

**Always validate before executing.** `hamilton_validate_dag` compiles the DAG without running it, catching:
- Syntax errors
- Missing dependencies (parameter names that don't match any function)
- Type annotation issues
- Circular references

```json
// Success response
{
  "valid": true,
  "node_count": 5,
  "nodes": ["cleaned", "feature_a", "feature_b", "raw_data", "result"],
  "inputs": ["data_path"],
  "errors": []
}
```

```json
// Failure response
{
  "valid": false,
  "node_count": 0,
  "nodes": [],
  "inputs": [],
  "errors": [{"type": "SyntaxError", "message": "...", "detail": "line 5"}]
}
```

**Self-correction loop:** If validation fails, read the error, fix the code, and validate again. Do not proceed to execution until validation passes.

### Step 4: Visualize the DAG (if graphviz available)

`hamilton_visualize` returns DOT graph source. Use this to:
- Confirm dependency structure matches intent
- Identify unexpected connections
- Explain the pipeline to the user

### Step 5: Explore Node Details

`hamilton_list_nodes` returns structured info for every node:
- Name, output type, documentation
- Whether it's an external input (must be provided at runtime)
- Required and optional dependencies

Use this to understand what inputs the DAG needs before execution.

### Step 6: Execute

`hamilton_execute` runs the DAG with provided inputs and returns results. Key parameters:
- `code`: The full Python source
- `final_vars`: List of node names to compute (only these and their dependencies run)
- `inputs`: Dict of external input values
- `timeout_seconds`: Safety limit (default 30s)

**WARNING:** This executes arbitrary Python code. Always validate first.

## Error Handling & Self-Correction

### Common Errors and Fixes

**"No module named 'X'"**
The code imports a library that isn't installed. Call `hamilton_capabilities` to check availability, then rewrite without the missing library.

**"Missing dependencies: ['node_name']"**
A function parameter doesn't match any function name or external input. Either:
1. Add a function with that name, or
2. Include it in `inputs` when executing

**"Execution timed out after Ns"**
The code takes too long. Reduce data size, simplify computation, or increase `timeout_seconds`.

**Validation passes but execution fails**
Validation checks structure, not runtime behavior. Common causes:
- Missing input values at execution time
- Runtime exceptions in function bodies (division by zero, key errors)
- Library-specific errors (e.g., column not found in DataFrame)

### Retry Strategy

1. If a tool returns an error, fix the issue in code and retry once
2. If the same error recurs, explain the issue to the user and ask for guidance
3. Never retry more than twice on the same error

## Tool Reference

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `hamilton_capabilities` | Environment discovery | **Always first** |
| `hamilton_scaffold` | Generate starter code | Starting a new pipeline |
| `hamilton_validate_dag` | Compile-time validation | Before every execution |
| `hamilton_list_nodes` | Inspect DAG structure | Understanding dependencies |
| `hamilton_visualize` | DOT graph generation | Explaining structure (requires graphviz) |
| `hamilton_execute` | Run the DAG | After successful validation |
| `hamilton_get_docs` | Hamilton documentation | Learning decorators, patterns |

## Environment Fallbacks

**If the MCP server is not running:**
Fall back to CLI:
```bash
# Validate a module
python -c "from hamilton import driver; import my_module; dr = driver.Builder().with_modules(my_module).build(); print('Valid!')"
```

**If Hamilton is not installed:**
Provide the user with installation instructions:
```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp   # Run via uvx (add --with <lib> as needed)
pip install "apache-hamilton[mcp]"              # Or install directly
```

## Success Criteria

A successful MCP interaction produces:
1. Code that passes `hamilton_validate_dag` with zero errors
2. All external inputs identified via `hamilton_list_nodes`
3. Execution results returned from `hamilton_execute`
4. The user understands the DAG structure (via visualization or node listing)

## Additional Resources

- For core Hamilton patterns: use `/hamilton-core`
- For scaling with async/Spark: use `/hamilton-scale`
- For LLM workflow patterns: use `/hamilton-llm`
- For observability: use `/hamilton-observability`
- Hamilton documentation: `hamilton_get_docs("overview")`
