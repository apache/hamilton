# Command line interface

This page covers the Apache Hamilton CLI. It is built directly from the CLI, but note that the command `hamilton --help` always provide the most accurate documentation.

## Installation
The dependencies for the Apache Hamilton CLI can be installed via

```console
pip install sf-hamilton[cli]
```

The CLI includes support for TOML files via the `tomli` library. When using TOML configuration files, the extra dependencies will be automatically available.

You can verify the installation with

```console
hamilton --help
```

## `hamilton` (global)

**Options**:

* `--verbose / --no-verbose`: [default: no-verbose]
* `--json-out / --no-json-out`: [default: no-json-out]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `build`: Build a single Driver with MODULES
* `diff`: Diff between the current MODULES and their specified GIT_REFERENCE
* `validate`: Validate DATAFLOW execution for the given CONTEXT
* `version`: Version NODES and DATAFLOW from dataflow with MODULES
* `view`: Build and visualize dataflow with MODULES

## `hamilton build`

Build a single Driver with MODULES

**Usage**:

```console
$ hamilton build [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

* `--name TEXT`: Name of the dataflow. Default: Derived from MODULES.
* `--context FILE`: Path to Driver context file [.json, .py, .toml]. For TOML files, Hamilton looks for either:
    - Top-level Hamilton headers: `HAMILTON_CONFIG`, `HAMILTON_FINAL_VARS`, `HAMILTON_INPUTS`, `HAMILTON_OVERRIDES`
    - Tool-specific section: `[tool.hamilton]` with `config`, `final_vars`, `inputs`, `overrides` sub-keys
* `--help`: Show this message and exit.

## `hamilton diff`

Diff between the current MODULES and their specified GIT_REFERENCE

**Usage**:

```console
$ hamilton diff [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

* `--name TEXT`: Name of the dataflow. Default: Derived from MODULES.
* `--context FILE`: Path to Driver context file [.json, .py, .toml]. For TOML files, Hamilton looks for either:
    - Top-level Hamilton headers: `HAMILTON_CONFIG`, `HAMILTON_FINAL_VARS`, `HAMILTON_INPUTS`, `HAMILTON_OVERRIDES`
    - Tool-specific section: `[tool.hamilton]` with `config`, `final_vars`, `inputs`, `overrides` sub-keys
* `--output-file-path PATH`: Output path of visualization. If path is a directory, use NAME for file name. [default: .]
* `--git-reference TEXT`: [default: HEAD]
* `--view / --no-view`: [default: no-view]
* `--help`: Show this message and exit.

## `hamilton validate`

Validate DATAFLOW execution for the given CONTEXT

**Usage**:

```console
$ hamilton validate [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

* `--context FILE`: [required] Path to Driver context file [.json, .py, .toml]. For TOML files, Hamilton looks for either:
    - Top-level Hamilton headers: `HAMILTON_CONFIG`, `HAMILTON_FINAL_VARS`, `HAMILTON_INPUTS`, `HAMILTON_OVERRIDES`
    - Tool-specific section: `[tool.hamilton]` with `config`, `final_vars`, `inputs`, `overrides` sub-keys
* `--name TEXT`: Name of the dataflow. Default: Derived from MODULES.
* `--help`: Show this message and exit.

## Using TOML Files for Configuration

Starting with version 2.0.0, the Hamilton CLI supports loading configuration from TOML files, including `pyproject.toml`. You can use either of these two formats:

### Format 1: Top-level Hamilton headers

In your TOML file, define the Hamilton configuration headers at the top level:

```toml
# example_context.toml
HAMILTON_CONFIG = {param1 = "value1", param2 = 42}
HAMILTON_FINAL_VARS = ["final_result", "output_value"]
HAMILTON_INPUTS = {input_value = 100, string_input = "example"}
HAMILTON_OVERRIDES = {override_param = "override_value"}
```

### Format 2: Tool-specific section (recommended for pyproject.toml)

For projects using `pyproject.toml`, it's recommended to place Hamilton configuration in the `[tool.hamilton]` section:

```toml
# pyproject.toml
[tool.hamilton]
config = {param1 = "value1", param2 = 42}
final_vars = ["final_result", "output_value"]
inputs = {input_value = 100, string_input = "example"}
overrides = {override_param = "override_value"}
```

### Usage

You can use TOML configuration files with all Hamilton CLI commands that support the `--context` option:

```console
hamilton build --context config.toml my_module.py
hamilton validate --context config.toml my_module.py
hamilton view --context config.toml my_module.py
hamilton diff --context config.toml my_module.py
hamilton version --context config.toml my_module.py
```

## `hamilton version`

Version NODES and DATAFLOW from dataflow with MODULES

**Usage**:

```console
$ hamilton version [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

* `--name TEXT`: Name of the dataflow. Default: Derived from MODULES.
* `--context FILE`: Path to Driver context file [.json, .py, .toml]. For TOML files, Hamilton looks for either:
    - Top-level Hamilton headers: `HAMILTON_CONFIG`, `HAMILTON_FINAL_VARS`, `HAMILTON_INPUTS`, `HAMILTON_OVERRIDES`
    - Tool-specific section: `[tool.hamilton]` with `config`, `final_vars`, `inputs`, `overrides` sub-keys
* `--help`: Show this message and exit.

## `hamilton view`

Build and visualize dataflow with MODULES

**Usage**:

```console
$ hamilton view [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

* `--name TEXT`: Name of the dataflow. Default: Derived from MODULES.
* `--context FILE`: Path to Driver context file [.json, .py, .toml]. For TOML files, Hamilton looks for either:
    - Top-level Hamilton headers: `HAMILTON_CONFIG`, `HAMILTON_FINAL_VARS`, `HAMILTON_INPUTS`, `HAMILTON_OVERRIDES`
    - Tool-specific section: `[tool.hamilton]` with `config`, `final_vars`, `inputs`, `overrides` sub-keys
* `--output-file-path PATH`: Output path of visualization. If path is a directory, use NAME for file name. [default: .]
* `--help`: Show this message and exit.
