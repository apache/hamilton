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

# Apache Hamilton Plugin for Claude Code

A comprehensive AI assistant skill for [Apache Hamilton](https://github.com/apache/hamilton) development, designed to help you build, debug, and optimize Apache Hamilton DAGs using Claude Code.

## What is This?

This is a [Claude Code plugin](https://code.claude.com/docs/en/plugins.md) that provides expert assistance for Apache Hamilton development. When active, Claude Code understands Apache Hamilton's patterns, best practices, and can help you:

- 🏗️ **Create new Apache Hamilton modules** with proper patterns and decorators
- 🔍 **Understand existing DAGs** by explaining dataflow and dependencies
- 🎨 **Apply function modifiers** correctly (@parameterize, @config.when, @check_output, etc.)
- 🐛 **Debug issues** in DAG definitions and execution
- 🔄 **Convert Python scripts** to Apache Hamilton modules
- ⚡ **Optimize pipelines** with caching, parallelization, and best practices
- ✅ **Write tests** for Apache Hamilton functions
- 📊 **Generate visualizations** of your DAGs

## Installation

### Option 1: Install via Plugin System (Recommended for Users)

```bash
# Add the Hamilton plugin marketplace
/plugin marketplace add apache/hamilton

# Install the plugin
/plugin install hamilton --scope user
```

Or in one command:
```bash
claude plugin install hamilton@apache/hamilton --scope user
```

**Installation scopes:**
- `--scope user` - Available in all your projects (recommended)
- `--scope project` - Only in current project
- `--scope local` - Testing/development only

### Option 2: For Apache Hamilton Contributors

If you've cloned the Apache Hamilton repository, the plugin is already available at `.claude-plugin/` and will be automatically discovered by Claude Code. No installation needed!

### Option 3: Manual Installation from Cloned Repo

Install the plugin from your local clone:

```bash
# From within the Hamilton repo directory
claude plugin install ./.claude-plugin --scope user

# Or copy the plugin directory
cp -r .claude-plugin ~/.claude/plugins/hamilton
```

## Usage

### Automatic Invocation

Claude Code will automatically use this skill when it detects you're working with Apache Hamilton code. Just ask questions or give instructions naturally:

```
"Help me create an Apache Hamilton module for processing customer data"
"Explain what this DAG does"
"Convert this pandas script to Apache Hamilton"
"Add caching to my expensive computation function"
"Why am I getting a circular dependency error?"
```

### Manual Invocation

You can explicitly invoke the skill using the `/hamilton` command:

```
/hamilton create a feature engineering module with rolling averages
/hamilton explain the dataflow in my_functions.py
/hamilton optimize this DAG for parallel execution
```

## What the Skill Knows

This skill has deep knowledge of:

- **Core Apache Hamilton concepts**: Drivers, DAGs, nodes, function-based definitions
- **Function modifiers**: All decorators (@parameterize, @config.when, @extract_columns, @check_output, @save_to, @load_from, @cache, @pipe, @does, @mutate, @step, etc.)
- **Execution patterns**: Sequential, parallel, distributed (Ray, Dask, Spark)
- **Data quality**: Validation, schema checking, data quality pipelines
- **I/O patterns**: Materialization, data loaders, result adapters
- **Integration patterns**: Airflow, Streamlit, FastAPI, Jupyter
- **LLM workflows**: RAG pipelines, document processing, embeddings
- **Testing strategies**: Unit testing functions, integration testing DAGs
- **Debugging techniques**: Circular dependencies, visualization, lineage tracing

## Examples

### Creating a New Apache Hamilton Module

```
"Create an Apache Hamilton module that loads data from a CSV, cleans it by removing
nulls, calculates a 7-day rolling average of the 'sales' column, and outputs
the top 10 days by sales."
```

Claude will generate:
- Properly structured functions with type hints
- Correct dependency declarations via parameters
- Appropriate docstrings
- Driver setup code
- Suggestions for visualization

### Converting Existing Code

```
"Convert this script to Apache Hamilton:

import pandas as pd
df = pd.read_csv('data.csv')
df['feature'] = df['col_a'] * 2 + df['col_b']
result = df.groupby('category')['feature'].mean()
"
```

Claude will refactor it into a clean Apache Hamilton module with separate functions for each transformation step.

### Applying Decorators

```
"I need to create rolling averages for 7, 30, and 90 day windows.
How do I do this in Apache Hamilton without repeating code?"
```

Claude will show you how to use `@parameterize` to create multiple nodes from a single function.

### Debugging

```
"I'm getting an error: 'Could not find parameter 'processed_data' in graph'.
What's wrong?"
```

Claude will help identify the issue (likely a typo or missing function definition) and suggest fixes.

## Skill Features

### Allowed Tools

This skill is configured with permissions to:
- Read files (`Read`, `Grep`, `Glob`)
- Run Python code (`Bash(python:*)`)
- Search for files (`Bash(find:*)`)
- Run tests (`Bash(pytest:*)`)

These tools are automatically permitted when the skill is active, streamlining the workflow.

### Reference Materials

The skill includes additional reference files:

- **[examples.md](skills/hamilton/examples.md)** - Comprehensive code examples for common patterns
  - Basic DAG creation
  - Advanced function modifiers
  - LLM & RAG workflows
  - Feature engineering patterns
  - Data quality validation
  - Parallel execution
  - Integration patterns (Airflow, FastAPI, Streamlit)

## Requirements

- **Claude Code CLI** - Install from https://code.claude.com
- **Apache Hamilton** - The skill works with any version, but references Hamilton 1.x+ patterns
- **Python 3.9+** - For running generated Apache Hamilton code

## Contributing

This plugin is open source and part of the Apache Hamilton project! We welcome contributions:

### Found a Bug?

Please [file an issue](https://github.com/apache/hamilton/issues/new) on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your Hamilton and Claude Code versions

### Want to Improve It?

Even better - submit a pull request!

1. **Fork the repository**: https://github.com/apache/hamilton
2. **Make your changes**: Edit files in `.claude-plugin/`
3. **Test thoroughly**: Try the skill with various Apache Hamilton scenarios
4. **Submit a PR**: Include a clear description of your improvements

**Types of contributions we love:**
- 📚 Add new examples to `examples.md`
- 📝 Improve instructions in `SKILL.md`
- 🐛 Fix bugs or inaccuracies
- ✨ Add support for new Apache Hamilton features
- 📖 Enhance documentation

See [CONTRIBUTING.md](../../../CONTRIBUTING.md) in the Apache Hamilton repo for detailed guidelines.

## Philosophy

This skill follows Apache Hamilton's core philosophy:

- **Declarative over imperative**: Guide users toward function-based definitions
- **Separation of concerns**: Keep definition, execution, and observation separate
- **Reusability**: Encourage patterns that make code testable and portable
- **Simplicity**: Prefer simple solutions over over-engineering

## Changelog

### v1.0.0 (2025-01-31)
- Initial release
- Comprehensive Apache Hamilton DAG creation assistance
- Support for all major function modifiers
- LLM/RAG workflow patterns
- Feature engineering examples
- Data quality validation patterns
- Integration examples (Airflow, FastAPI, Streamlit)

## Learn More

- **Apache Hamilton Documentation**: https://hamilton.apache.org
- **GitHub Repository**: https://github.com/apache/hamilton
- **Apache Hamilton Examples**: See `examples/` directory in the repo (60+ production examples)
- **DAGWorks Blog**: https://blog.dagworks.io
- **Community Slack**: Join via Apache Hamilton GitHub repo

## License

This plugin is part of the Apache Hamilton project and is licensed under the Apache 2.0 License.

---

**Happy Apache Hamilton coding with Claude! 🚀**
