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

# MCP Server

The Hamilton MCP server exposes Hamilton's DAG compilation, validation, and execution as tools for LLM clients via the [Model Context Protocol](https://modelcontextprotocol.io/) (MCP). It enables LLM-driven development workflows where you write Hamilton functions, validate the DAG, visualize dependencies, and execute pipelines -- all through natural language interaction with clients such as Claude Desktop, Claude Code, or Cursor.

## Architecture

```{mermaid}
graph LR
    A[LLM Client] -->|MCP stdio transport| B[Hamilton MCP Server]
    B -->|build & execute| C[Hamilton Driver]
    C -->|compile DAG from| D[User Code]
```

The server runs as a local process using **stdio transport**. The LLM client launches the server, sends tool calls over stdin/stdout, and receives structured JSON responses. Internally, the server compiles user-provided Python source into a Hamilton DAG via `hamilton.driver.Builder` (with dynamic execution enabled), then performs the requested operation (validate, list nodes, visualize, or execute).

## Installation

The recommended way to run the MCP server is via `uvx`, which handles installation automatically:

```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp
```

This creates an ephemeral environment with Hamilton and [FastMCP](https://github.com/PrefectHQ/fastmcp), runs the server, and cleans up after. No pre-installation required.

Alternatively, install into your own environment:

```bash
pip install "apache-hamilton[mcp]"
```

### Optional dependencies

The server can compile and execute user code, so any libraries your code imports must be available in the server's environment. When using `uvx`, pass `--with` to include them:

| Library | Install command | What it enables |
|---------|----------------|-----------------|
| pandas | `pip install pandas` | DataFrame-based scaffold templates and result serialization |
| numpy | `pip install numpy` | ML pipeline scaffolds and ndarray serialization |
| polars | `pip install polars` | Polars DataFrame/Series serialization |
| graphviz | `pip install "apache-hamilton[visualization]"` | DAG visualization via `hamilton_visualize` |

For example, for a pandas/numpy project:

```bash
uvx --from "apache-hamilton[mcp]" --with pandas --with numpy hamilton-mcp
```

Or for a polars project:

```bash
uvx --from "apache-hamilton[mcp]" --with polars hamilton-mcp
```

## Running the Server

### Via uvx (recommended)

```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp
```

Include the libraries your code uses via `--with`:

```bash
# pandas/numpy project
uvx --from "apache-hamilton[mcp]" --with pandas --with numpy hamilton-mcp

# polars project
uvx --from "apache-hamilton[mcp]" --with polars hamilton-mcp
```

### Direct CLI

If Hamilton is already installed in your environment:

```bash
hamilton-mcp
```

### Programmatic

You can also start the server from Python:

```python
from hamilton.plugins.h_mcp import get_mcp_server

mcp = get_mcp_server()
mcp.run()
```

The `get_mcp_server()` function returns a `FastMCP` instance. Call `.run()` to start the stdio transport loop.

## Connecting to an LLM Client

### Claude Desktop

Add the following to your Claude Desktop configuration file (`claude_desktop_config.json`). Add `"--with", "<library>"` pairs for whichever libraries your code uses:

```json
{
  "mcpServers": {
    "hamilton": {
      "command": "uvx",
      "args": [
        "--from", "apache-hamilton[mcp]",
        "--with", "pandas",
        "--with", "numpy",
        "hamilton-mcp"
      ]
    }
  }
}
```

### Claude Code

Add the server to your project configuration, including `--with` flags for your libraries:

```bash
claude mcp add hamilton -- uvx --from "apache-hamilton[mcp]" --with pandas --with numpy hamilton-mcp
```

Or add it to your `.mcp.json` file:

```json
{
  "mcpServers": {
    "hamilton": {
      "command": "uvx",
      "args": [
        "--from", "apache-hamilton[mcp]",
        "--with", "pandas",
        "--with", "numpy",
        "hamilton-mcp"
      ]
    }
  }
}
```

See also the [Claude Code Plugin](claude-code-plugin.md) for an accompanying skill that provides workflow guidance when using the MCP tools.

### Cursor

In Cursor, open **Settings > MCP Servers** and add (adjust `--with` flags to match your project):

```json
{
  "hamilton": {
    "command": "uvx",
    "args": [
      "--from", "apache-hamilton[mcp]",
      "--with", "pandas",
      "--with", "numpy",
      "hamilton-mcp"
    ]
  }
}
```

### Other MCP-compatible clients

Any client that supports the MCP stdio transport can connect by launching the server as a subprocess. The server reads JSON-RPC messages from stdin and writes responses to stdout.

```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp
```

Add `--with <library>` for any libraries your code imports (e.g., `--with pandas --with numpy` or `--with polars`).

## Available Tools

The server exposes seven tools. Each tool accepts and returns JSON.

### `hamilton_capabilities`

Report which optional libraries are installed and which features are available. Call this first to discover the environment before generating code. If the user specifies which libraries they use, pass them as `preferred_libraries` to filter scaffold patterns accordingly.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `preferred_libraries` | `list[str] \| None` | No | Libraries the user wants to use (e.g., `["pandas", "numpy"]`). When provided, scaffolds are filtered to only those whose requirements are a subset of this list. When omitted, falls back to auto-detection. |

**Returns:** A dict with `libraries` (library name to boolean, reflecting what is installed) and `available_scaffolds` (list of scaffold pattern names filtered by preference or auto-detection).

---

### `hamilton_validate_dag`

Validate Hamilton DAG code by building the Driver. Compiles Python source into a Hamilton DAG and checks for missing dependencies, type mismatches, and circular references without executing the code.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `str` | Yes | Python source code defining Hamilton functions |
| `config` | `dict \| None` | No | Hamilton config dict passed to `Builder.with_config()` |

**Returns:** `{"valid": true, "node_count": N, "nodes": [...], "inputs": [...], "errors": []}` on success, or `{"valid": false, "node_count": 0, "nodes": [], "inputs": [], "errors": [...]}` on failure. Each error is a dict with `type`, `message`, `detail` (may be `null` for non-syntax errors), and `traceback` fields.

---

### `hamilton_list_nodes`

List all nodes in a Hamilton DAG with their types and dependencies. Returns structured info for every node including name, output type, tags, whether it is an external input, and its required/optional dependencies.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `str` | Yes | Python source code defining Hamilton functions |
| `config` | `dict \| None` | No | Hamilton config dict passed to `Builder.with_config()` |

**Returns:** `{"nodes": [...], "errors": []}`. Each node is a dict with `name`, `type`, `is_external_input`, `tags`, `required_dependencies`, `optional_dependencies`, and `documentation` fields.

---

### `hamilton_visualize`

Visualize the Hamilton DAG as DOT graph source. Requires `graphviz` (`pip install "apache-hamilton[visualization]"`).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `str` | Yes | Python source code defining Hamilton functions |
| `config` | `dict \| None` | No | Hamilton config dict passed to `Builder.with_config()` |
| `output_format` | `str` | No | Output format (default: `"dot"`). Currently only `"dot"` is supported; other values are accepted but ignored. |

**Returns:** A string containing the Graphviz DOT source for the dependency graph, or an error message if graphviz is not installed.

---

### `hamilton_execute`

Execute a Hamilton DAG and return the requested outputs. Builds the DAG from source, then calls `driver.execute()` with the given `final_vars` and `inputs`. Results are serialized to JSON-safe values. A timeout (default 30 seconds) guards against long-running code.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | `str` | Yes | Python source code defining Hamilton functions |
| `final_vars` | `list[str]` | Yes | Node names to compute |
| `inputs` | `dict \| None` | No | External input values |
| `config` | `dict \| None` | No | Hamilton config dict passed to `Builder.with_config()` |
| `timeout_seconds` | `int` | No | Execution timeout in seconds (default: `30`) |

**Returns:** `{"results": {...}, "execution_time_ms": N}` on success. On failure: `{"error": "..."}` for build errors or timeouts, or `{"error": "...", "execution_time_ms": N}` for runtime errors during execution. Results are serialized: pandas DataFrames/Series become dicts via `.to_dict()`, numpy arrays become lists via `.tolist()`, polars DataFrames become list-of-dicts via `.to_dicts()`, polars Series become lists via `.to_list()`, and all other types use `str()`.

**Warning:** This tool executes arbitrary Python code. Always validate with `hamilton_validate_dag` before executing.

---

### `hamilton_get_docs`

Get Hamilton documentation for a specific topic.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | `str` | Yes | One of: `overview`, `decorators`, `driver`, `builder`, or any decorator name (`parameterize`, `extract_columns`, `config`, `check_output`, `tag`, `pipe`, `does`, `subdag`, etc.) |

**Returns:** A string containing the requested documentation.

---

### `hamilton_scaffold`

Generate a starter Hamilton module for a given pattern. Available patterns depend on installed or preferred libraries. Returns Python source code that is a valid Hamilton module, plus a driver script example.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pattern` | `str` | Yes | Scaffold pattern name (use `hamilton_capabilities` to discover available patterns) |
| `preferred_libraries` | `list[str] \| None` | No | Libraries the user wants to use. Filters available patterns the same way as in `hamilton_capabilities`. |

**Returns:** A string containing Python source code for the requested scaffold pattern, or an error listing available patterns if the name is invalid.

**Available scaffold patterns:**

| Pattern | Required libraries | Description |
|---------|-------------------|-------------|
| `basic_pure_python` | None | Simple data processing pipeline using only built-in Python types |
| `basic` | pandas | DataFrame cleaning and row counting |
| `parameterized` | pandas | Using `@parameterize` to create multiple nodes from one function |
| `config_based` | pandas | Conditional logic with `@config.when` |
| `data_pipeline` | pandas | ETL workflow: ingest, clean, transform, aggregate |
| `ml_pipeline` | pandas, numpy | Feature engineering and train/test split |
| `data_quality` | pandas, numpy | Data validation with `@check_output` |

## Conditional Features

The MCP server adapts to the libraries installed in the current Python environment. At startup, it probes for four optional libraries:

- **pandas** -- Enables DataFrame-based scaffold templates and DataFrame/Series result serialization
- **numpy** -- Enables the ML pipeline and data quality scaffolds, plus ndarray serialization
- **polars** -- Enables Polars DataFrame/Series result serialization
- **graphviz** -- Enables DAG visualization via `hamilton_visualize`

The `hamilton_capabilities` tool reports which libraries are installed. Both `hamilton_capabilities` and `hamilton_scaffold` accept an optional `preferred_libraries` parameter: when provided, scaffolds are filtered to match the user's stated preferences rather than relying on auto-detection. This is especially useful with `uvx`, where the server runs in an ephemeral environment that may not reflect the user's project.

When no preference is given, the tools fall back to auto-detecting installed libraries.

## Usage Examples

### Example 1: Ask the user, discover capabilities, and scaffold

Start by asking which libraries the user works with, then pass their preferences:

```
User: I want to build a Hamilton pipeline.

LLM: Which data libraries do you use? (e.g., pandas, numpy, polars)

User: I use pandas.

Tool call: hamilton_capabilities(preferred_libraries=["pandas"])
Response:
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

Tool call: hamilton_scaffold(pattern="data_pipeline", preferred_libraries=["pandas"])
Response:
"""Hamilton data pipeline: ingest -> clean -> transform -> aggregate."""
import pandas as pd

def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
    """Ingest raw data."""
    return raw_data_input

def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Remove nulls and duplicates."""
    return raw_data.dropna().drop_duplicates()
...
```

### Example 2: Validate and fix, then execute

Write code, validate it, fix errors, and run:

```
Tool call: hamilton_validate_dag(
  code="""
import pandas as pd

def raw_data(raw_data_input: pd.DataFrame) -> pd.DataFrame:
    return raw_data_input

def cleaned(raw_data: pd.DataFrame) -> pd.DataFrame:
    return raw_data.dropna()

def row_count(cleaned: pd.DataFrame) -> int:
    return len(cleaned)
"""
)
Response:
{
  "valid": true,
  "node_count": 3,
  "nodes": ["cleaned", "raw_data", "row_count"],
  "inputs": ["raw_data_input"],
  "errors": []
}

Tool call: hamilton_execute(
  code="...(same code)...",
  final_vars=["row_count"],
  inputs={"raw_data_input": {"a": [1, 2, None], "b": [4, None, 6]}}
)
Response:
{
  "results": {"row_count": "1"},
  "execution_time_ms": 12.3
}
```

### Example 3: Explore documentation on decorators

```
Tool call: hamilton_get_docs(topic="parameterize")
Response:
@parameterize

Creates multiple nodes from a single function definition.
Each parameterization defines a new node name and the argument
values to pass to the function...
```

## Recommended Workflow

The server instructions recommend the following sequence for interactive DAG development:

```
ask user -> capabilities -> scaffold -> validate -> visualize -> correct -> execute
```

1. **Ask the user** -- Ask which data libraries they use (pandas, numpy, polars, etc.), then pass the answer as `preferred_libraries` to capabilities and scaffold.
2. **Capabilities** -- Call `hamilton_capabilities` to discover the environment.
3. **Scaffold** -- Use `hamilton_scaffold` to generate a starting point matched to the user's preferred libraries.
4. **Validate** -- Call `hamilton_validate_dag` to compile the DAG without executing it.
5. **Visualize** -- Call `hamilton_visualize` to inspect the dependency graph (requires graphviz).
6. **Correct** -- If validation fails, read the error, fix the code, and validate again.
7. **Execute** -- Call `hamilton_execute` after validation passes.

## Accompanying Claude Code Skill

The Hamilton [Claude Code Plugin](claude-code-plugin.md) includes a dedicated **hamilton-mcp** skill that provides workflow guidance for using the MCP tools. The skill is defined in `.claude-plugin/skills/mcp/SKILL.md` and is registered in the plugin manifest.

The skill provides:

- **Golden path workflow** -- Step-by-step instructions for the capabilities-scaffold-validate-visualize-correct-execute loop
- **Decision rules** -- Guidance on choosing scaffolds based on available libraries
- **Error handling strategy** -- Common errors, their causes, and fixes (missing modules, missing dependencies, timeouts, runtime vs. validation failures)
- **Retry policy** -- Retry once on error, explain to the user on second failure, never retry more than twice on the same error
- **Success criteria** -- A clear definition of what constitutes a successful interaction: zero validation errors, all inputs identified, results returned, and the user understands the DAG structure

When Claude Code detects the Hamilton MCP server, the skill activates automatically and guides the LLM through best-practice usage of the tools.

## Troubleshooting

### `ModuleNotFoundError: FastMCP is required`

The MCP extra is not installed. Use `uvx` which handles installation automatically:

```bash
uvx --from "apache-hamilton[mcp]" hamilton-mcp
```

Or install manually: `pip install "apache-hamilton[mcp]"`

### `hamilton-mcp: command not found`

If running directly (without `uvx`), the CLI entrypoint may not be on your `PATH`. Either use `uvx` (recommended), activate the virtual environment where Hamilton is installed, or use the full path:

```bash
/path/to/your/venv/bin/hamilton-mcp
```

### Visualization returns an error

The `hamilton_visualize` tool requires the `graphviz` Python package and the Graphviz system binary. Install both:

```bash
pip install "apache-hamilton[visualization]"

# On Ubuntu/Debian:
sudo apt-get install graphviz

# On macOS:
brew install graphviz
```

### Execution times out

The default timeout is 30 seconds. For long-running pipelines, pass a higher `timeout_seconds` value to `hamilton_execute`. Alternatively, reduce the data size or simplify the computation.

### Validation passes but execution fails

Validation checks DAG structure (dependencies, types, circular references) but does not run function bodies. Common runtime failures include:

- Missing input values not provided in the `inputs` dict
- Exceptions inside function bodies (division by zero, key errors)
- Library-specific errors (e.g., column not found in a DataFrame)

## Learn More

- [Hamilton documentation](https://hamilton.apache.org) -- Full framework reference
- [Claude Code Plugin](claude-code-plugin.md) -- AI-powered Hamilton development in Claude Code
- [CLI reference](../how-tos/cli-reference.md) -- The `hamilton` CLI for build, diff, version, and view
- [Model Context Protocol](https://modelcontextprotocol.io/) -- MCP specification and ecosystem
