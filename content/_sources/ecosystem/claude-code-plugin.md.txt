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

# Claude Code Plugin for Hamilton

The Hamilton Claude Code plugin provides AI-powered assistance for developing Hamilton DAGs using [Claude Code](https://code.claude.com), Anthropic's official CLI tool.

## What is Claude Code?

[Claude Code](https://code.claude.com) is an AI-powered CLI tool that helps you build software faster by providing intelligent code assistance, debugging help, and code generation capabilities. The Hamilton plugin extends Claude Code with deep knowledge of Hamilton patterns and best practices.

## Features

The Hamilton Claude Code plugin provides expert assistance for:

- 🏗️ **Creating new Hamilton modules** with proper patterns and decorators
- 🔍 **Understanding existing DAGs** by explaining dataflow and dependencies
- 🎨 **Applying function modifiers** correctly (@parameterize, @config.when, @check_output, etc.)
- 🐛 **Debugging issues** in DAG definitions and execution
- 🔄 **Converting Python scripts** to Hamilton modules
- ⚡ **Optimizing pipelines** with caching, parallelization, and best practices
- ✅ **Writing tests** for Hamilton functions
- 📊 **Generating visualizations** of your DAGs

## Installation

### Prerequisites

First, install Claude Code:

```bash
# Install Claude Code CLI
curl -fsSL https://cli.claude.ai/install.sh | sh
```

For more installation options, see the [Claude Code documentation](https://code.claude.com/docs/en/install.html).

### Install the Hamilton Plugin

Once Claude Code is installed, you can add the Hamilton plugin:

```bash
# Add the Hamilton plugin marketplace
/plugin marketplace add apache/hamilton

# Install the plugin (available across all projects)
/plugin install hamilton --scope user
```

Or combine into a single command:
```bash
claude plugin install hamilton@apache/hamilton --scope user
```

**Installation scopes:**
- `--scope user` - Available in all your projects (recommended)
- `--scope project` - Only in the current project
- `--scope local` - Testing/development only

### For Contributors

If you've cloned the Hamilton repository, the skill is already available in `.claude/plugins/hamilton/skills/hamilton/` and will be automatically discovered by Claude Code when you work in the repo. No installation needed!

## Usage

### Automatic Assistance

Claude Code will automatically use the Hamilton plugin when it detects you're working with Hamilton code. Just ask questions or give instructions naturally:

```bash
claude "Help me create a Hamilton module for processing customer data"
claude "Explain what this DAG does"
claude "Convert this pandas script to Hamilton"
claude "Add caching to my expensive computation function"
claude "Why am I getting a circular dependency error?"
```

### Manual Invocation

You can explicitly invoke the skill using the `/hamilton` command:

```bash
claude /hamilton create a feature engineering module with rolling averages
claude /hamilton explain the dataflow in my_functions.py
claude /hamilton optimize this DAG for parallel execution
```

### Interactive Mode

For ongoing assistance, start an interactive session:

```bash
# Start Claude Code in your Hamilton project
cd /path/to/your/hamilton/project
claude
```

Then interact naturally:
```
You: I need to create a DAG that processes customer transactions
Claude: I'll help you create a Hamilton module for processing customer transactions...

You: Add validation to ensure all amounts are positive
Claude: I'll add a @check_output decorator with validation...
```

## Examples

### Creating a New Hamilton Module

**Prompt:**
```
Create a Hamilton module that loads sales data from a CSV, removes nulls,
calculates a 7-day rolling average, and outputs the top 10 days by sales.
```

**Claude generates:**
```python
"""Sales analysis DAG."""
import pandas as pd

def raw_sales(csv_path: str) -> pd.DataFrame:
    """Load sales data from CSV.

    :param csv_path: Path to sales CSV file
    :return: Raw sales DataFrame
    """
    return pd.read_csv(csv_path)

def cleaned_sales(raw_sales: pd.DataFrame) -> pd.DataFrame:
    """Remove null values from sales data.

    :param raw_sales: Raw sales data
    :return: Cleaned sales DataFrame
    """
    return raw_sales.dropna()

def rolling_avg_7d(cleaned_sales: pd.DataFrame) -> pd.Series:
    """Calculate 7-day rolling average of sales.

    :param cleaned_sales: Cleaned sales data
    :return: 7-day rolling average
    """
    return cleaned_sales['sales'].rolling(window=7, min_periods=1).mean()

def top_10_sales_days(
    cleaned_sales: pd.DataFrame,
    rolling_avg_7d: pd.Series
) -> pd.DataFrame:
    """Get top 10 days by rolling average.

    :param cleaned_sales: Cleaned sales data
    :param rolling_avg_7d: 7-day rolling average
    :return: Top 10 sales days
    """
    result = cleaned_sales.copy()
    result['rolling_avg'] = rolling_avg_7d
    return result.nlargest(10, 'rolling_avg')

# Usage:
# from hamilton import driver
# dr = driver.Driver({}, __name__)
# results = dr.execute(['top_10_sales_days'], inputs={'csv_path': 'sales.csv'})
```

### Converting Existing Code

**Prompt:**
```
Convert this script to Hamilton:

import pandas as pd
df = pd.read_csv('data.csv')
df['feature'] = df['col_a'] * 2 + df['col_b']
result = df.groupby('category')['feature'].mean()
```

**Claude refactors to:**
```python
"""Data processing DAG."""
import pandas as pd

def raw_data(data_path: str) -> pd.DataFrame:
    """Load raw data from CSV."""
    return pd.read_csv(data_path)

def feature(raw_data: pd.DataFrame) -> pd.Series:
    """Calculate feature from columns."""
    return raw_data['col_a'] * 2 + raw_data['col_b']

def data_with_feature(raw_data: pd.DataFrame, feature: pd.Series) -> pd.DataFrame:
    """Add feature column to dataset."""
    result = raw_data.copy()
    result['feature'] = feature
    return result

def result(data_with_feature: pd.DataFrame) -> pd.Series:
    """Calculate mean feature by category."""
    return data_with_feature.groupby('category')['feature'].mean()
```

### Applying Decorators

**Prompt:**
```
I need to create rolling averages for 7, 30, and 90 day windows.
How do I do this without repeating code?
```

**Claude suggests:**
```python
from hamilton.function_modifiers import parameterize

@parameterize(
    rolling_7d={'window': 7},
    rolling_30d={'window': 30},
    rolling_90d={'window': 90},
)
def rolling_average(sales: pd.Series, window: int) -> pd.Series:
    """Calculate rolling average for different windows.

    Creates three nodes: rolling_7d, rolling_30d, rolling_90d
    """
    return sales.rolling(window=window, min_periods=1).mean()
```

### Debugging

**Prompt:**
```
I'm getting: "Could not find parameter 'processed_data' in graph"
```

**Claude analyzes:**
```
This error occurs when a function parameter references a node that doesn't exist
in your DAG. Common causes:

1. Typo in parameter name (e.g., 'processed_data' vs 'process_data')
2. Missing function definition for 'processed_data'
3. Function excluded via @hamilton_exclude or @config.when

Check your module for a function named 'processed_data'. If it doesn't exist,
either:
- Add the function, or
- Fix the parameter name to match an existing function
```

## What the Plugin Knows

The plugin has deep knowledge of Hamilton:

### Core Concepts
- Function-based DAG definitions
- Driver configuration and execution
- Node dependencies via parameters
- Type hints and annotations

### Function Modifiers
- **Configuration**: @config.when, @hamilton_exclude
- **Parameterization**: @parameterize, @parameterize_sources, @parameterize_values
- **Column extraction**: @extract_columns, @extract_fields
- **Data quality**: @check_output, @check_output_custom, @schema
- **I/O**: @save_to, @load_from, @dataloader, @datasaver
- **Transformation**: @pipe, @does, @mutate, @step
- **Advanced**: @subdag, @resolve, @cache

### Integration Patterns
- Airflow orchestration
- FastAPI microservices
- Streamlit dashboards
- Jupyter notebooks
- Ray/Dask/Spark distributed execution

### LLM Workflows
- RAG pipeline patterns
- Document chunking
- Vector database operations
- Embedding generation

### Best Practices
- Testing strategies
- Code organization
- Error handling
- Performance optimization

## Plugin Structure

The plugin is organized as follows:

```
.claude/plugins/hamilton/
├── .claude-plugin/
│   ├── plugin.json           # Plugin manifest
│   └── marketplace.json      # Marketplace configuration
├── skills/
│   └── hamilton/
│       ├── SKILL.md          # Main skill instructions
│       ├── examples.md       # Code examples and patterns
│       └── README.md         # Skill documentation
└── README.md                 # Plugin documentation
```

For contributors, the skill exists in `.claude/plugins/hamilton/skills/hamilton/` for immediate use.

## Contributing

Found a bug or want to improve the plugin? We'd love your help!

### Report Issues

Please [file an issue](https://github.com/apache/hamilton/issues/new) with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Hamilton and Claude Code versions

### Submit Pull Requests

1. Fork the repository: https://github.com/apache/hamilton
2. Make changes in `.claude/plugins/hamilton/skills/hamilton/`
3. Test thoroughly with various scenarios
4. Submit a PR with a clear description

**Contribution ideas:**
- 📚 Add new examples to `examples.md`
- 📝 Improve instructions in `SKILL.md`
- 🐛 Fix bugs or inaccuracies
- ✨ Add support for new Hamilton features
- 📖 Enhance documentation

See [CONTRIBUTING.md](https://github.com/apache/hamilton/blob/main/CONTRIBUTING.md) for guidelines.

## Requirements

- **Claude Code CLI** - v0.1.0 or later
- **Hamilton** - v1.0.0 or later (plugin works with any version)
- **Python** - 3.9 or later

## Troubleshooting

### Plugin Not Loading

If the plugin isn't recognized:

```bash
# Check installed plugins
claude plugin list

# Reinstall if needed
claude plugin uninstall hamilton
claude plugin install hamilton@apache/hamilton --scope user
```

### Skill Not Activating

If Claude doesn't seem to use Hamilton knowledge:

```bash
# Manually invoke the skill
claude /hamilton <your-question>

# Or mention Hamilton explicitly in your prompt
claude "Using Hamilton framework, create a DAG for..."
```

### Permission Errors

The plugin requests permission to:
- Read files (Read, Grep, Glob)
- Run Python code (python, pytest)
- Search files (find)

If prompted, approve these permissions for the best experience.

## Learn More

- **Hamilton Documentation**: https://hamilton.apache.org
- **Claude Code Documentation**: https://code.claude.com/docs
- **Hamilton GitHub**: https://github.com/apache/hamilton
- **Hamilton Examples**: https://github.com/apache/hamilton/tree/main/examples
- **Community Slack**: Join via Hamilton GitHub repo

## License

This plugin is part of the Apache Hamilton project and is licensed under the Apache 2.0 License.

---

**Enhance your Hamilton development with AI! 🚀**
