# Command line interface

This page covers the Apache Hamilton CLI. It is built directly from the CLI, but note that the command `hamilton --help` always provide the most accurate documentation.

## Installation
The dependencies for the Apache Hamilton CLI can be installed via

```console
pip install sf-hamilton[cli]
```

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
* `diff`: Diff between the current MODULES and their...
* `version`: Version NODES and DATAFLOW from dataflow...
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

* `--git-reference TEXT`: [default: HEAD]
* `--view / --no-view`: [default: no-view]
* `--output-file-path PATH`: [default: diff.png]
* `--help`: Show this message and exit.

## `hamilton version`

Version NODES and DATAFLOW from dataflow with MODULES

**Usage**:

```console
$ hamilton version [OPTIONS] MODULES...
```

**Arguments**:

* `MODULES...`: [required]

**Options**:

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

* `--output-file-path PATH`: [default: ./dag.png]
* `--help`: Show this message and exit.
