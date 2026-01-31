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
name: hamilton-core
description: Core Hamilton patterns for creating DAGs, applying decorators, testing, and debugging dataflows. Use for basic Hamilton development tasks.
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(pytest:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton Core Development Assistant

Apache Hamilton is a lightweight Python framework for building Directed Acyclic Graphs (DAGs) of data transformations using declarative, function-based definitions.

## Core Principles

**Function-Based DAG Definition**
- Functions with type hints define nodes in the DAG
- Function parameters automatically create edges (dependencies)
- Function names become node names in the DAG
- Pure functions enable easy testing and reusability

**Key Architecture Components**
- **Functions**: Define transformations with parameters as dependencies
- **Driver**: Builds and manages DAG execution (`.execute()` runs the DAG)
- **FunctionGraph**: Internal DAG representation
- **Function Modifiers**: Decorators that modify DAG behavior
- **Adapters**: Result formatters and lifecycle hooks

**Separation of Concerns**
- **Definition layer**: Pure Python functions (testable, reusable)
- **Execution layer**: Driver configuration (where/how to run)
- **Observation layer**: Monitoring, lineage, caching

## Common Tasks

### 1. Creating New Hamilton Modules

**Basic Module Structure:**
```python
"""
Module docstring explaining the DAG's purpose.
"""
import pandas as pd
from hamilton.function_modifiers import extract_columns

def raw_data(data_path: str) -> pd.DataFrame:
    """Load raw data from source.

    :param data_path: Path to data file (passed as input)
    :return: Raw DataFrame
    """
    return pd.read_csv(data_path)

def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Remove null values and duplicates.

    :param raw_data: Raw data from previous node
    :return: Cleaned DataFrame
    """
    return raw_data.dropna().drop_duplicates()

def feature_a(cleaned_data: pd.DataFrame) -> pd.Series:
    """Calculate feature A.

    :param cleaned_data: Cleaned data
    :return: Feature A values
    """
    return cleaned_data['column_a'] * 2
```

**Driver Setup:**
```python
from hamilton import driver
import my_functions

dr = driver.Driver({}, my_functions)
results = dr.execute(
    ['feature_a', 'cleaned_data'],
    inputs={'data_path': 'data.csv'}
)
```

**Best Practices:**
1. ✅ Add type hints to ALL function signatures
2. ✅ Write clear docstrings with :param and :return
3. ✅ Keep functions pure (no side effects)
4. ✅ Name functions after the output they produce
5. ✅ Use function parameters for dependencies (not globals)
6. ✅ Create unit tests for each function
7. ❌ Don't use classes unless needed (functions are preferred)
8. ❌ Don't mutate inputs (return new objects)

### 2. Applying Function Modifiers (Decorators)

**Configuration & Polymorphism:**
```python
from hamilton.function_modifiers import config

@config.when(model_type='linear')
def predictions(features: pd.DataFrame) -> pd.Series:
    """Linear model predictions."""
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    return model.fit_predict(features)

@config.when(model_type='tree')
def predictions(features: pd.DataFrame) -> pd.Series:
    """Tree model predictions."""
    from sklearn.tree import DecisionTreeRegressor
    model = DecisionTreeRegressor()
    return model.fit_predict(features)

# Use: driver.Driver({'model_type': 'linear'}, module)
```

**Parameterization - Creating Multiple Nodes:**
```python
from hamilton.function_modifiers import parameterize

@parameterize(
    rolling_7d={'window': 7},
    rolling_30d={'window': 30},
    rolling_90d={'window': 90},
)
def rolling_average(spend: pd.Series, window: int) -> pd.Series:
    """Calculate rolling average for different windows."""
    return spend.rolling(window).mean()

# Creates 3 nodes: rolling_7d, rolling_30d, rolling_90d
```

**Column Extraction - DataFrames to Series:**
```python
from hamilton.function_modifiers import extract_columns

@extract_columns('feature_1', 'feature_2', 'feature_3')
def features(cleaned_data: pd.DataFrame) -> pd.DataFrame:
    """Generate multiple features."""
    return pd.DataFrame({
        'feature_1': cleaned_data['a'] * 2,
        'feature_2': cleaned_data['b'] ** 2,
        'feature_3': cleaned_data['a'] + cleaned_data['b'],
    })

# Creates 3 nodes: feature_1, feature_2, feature_3 (each a Series)
```

**Data Quality Validation:**
```python
from hamilton.function_modifiers import check_output
import pandera as pa

@check_output(
    data_type=float,
    range=(0, 100),
    importance="fail"
)
def revenue_percentage(revenue: float, total: float) -> float:
    """Calculate revenue as percentage."""
    return (revenue / total) * 100

# With Pandera schemas
@check_output(
    schema=pa.SeriesSchema(float, pa.Check.greater_than(0)),
    importance="fail"
)
def positive_values(data: pd.Series) -> pd.Series:
    """Ensure all values are positive."""
    return data
```

**I/O Materialization:**
```python
from hamilton.function_modifiers import save_to, load_from
from hamilton.io.materialization import to

@save_to(to.csv(path="output.csv"))
def final_results(aggregated_data: pd.DataFrame) -> pd.DataFrame:
    """Save final results to CSV."""
    return aggregated_data

@load_from(from_='data.parquet', reader='parquet')
def input_data() -> pd.DataFrame:
    """Load data from parquet."""
    pass  # Function body ignored when using @load_from
```

### 3. Converting Existing Code to Hamilton

**Before (Script):**
```python
import pandas as pd

df = pd.read_csv('data.csv')
df = df.dropna()
df['feature'] = df['col_a'] * 2
result = df.groupby('category')['feature'].mean()
print(result)
```

**After (Hamilton Module):**
```python
"""Data processing DAG."""
import pandas as pd

def raw_data(data_path: str) -> pd.DataFrame:
    """Load raw data."""
    return pd.read_csv(data_path)

def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Remove nulls."""
    return raw_data.dropna()

def feature(cleaned_data: pd.DataFrame) -> pd.Series:
    """Calculate feature."""
    return cleaned_data['col_a'] * 2

def data_with_feature(cleaned_data: pd.DataFrame, feature: pd.Series) -> pd.DataFrame:
    """Add feature to dataset."""
    df = cleaned_data.copy()
    df['feature'] = feature
    return df

def result(data_with_feature: pd.DataFrame) -> pd.Series:
    """Aggregate by category."""
    return data_with_feature.groupby('category')['feature'].mean()
```

**Conversion Guidelines:**
1. Identify distinct computation steps
2. Extract each step into a pure function
3. Use previous step's variable name as function parameter
4. Add type hints and docstrings
5. Remove imperative variable assignments
6. Test each function independently

### 4. Visualizing & Understanding DAGs

**Generate Visualization:**
```python
from hamilton import driver
import my_functions

dr = driver.Driver({}, my_functions)

# Create visualization
dr.display_all_functions('dag.png')  # All nodes
dr.visualize_execution(
    ['final_output'],
    'execution.png',
    inputs={'input_data': ...}
)  # Execution path only
```

**Understanding DAG Structure:**
- Each function becomes a node
- Function parameters create directed edges
- No cycles allowed (DAG = Directed Acyclic Graph)
- Execution order determined by dependencies
- Multiple paths execute in parallel when possible

**Debugging Tips:**
1. Check for circular dependencies (A depends on B depends on A)
2. Verify all parameter names match existing function names
3. Look for typos in parameter names
4. Use `dr.list_available_variables()` to see all nodes
5. Check `dr.what_is_downstream_of('node_name')` for dependencies

### 5. Testing Hamilton Functions

**Unit Testing Pattern:**
```python
import pytest
import pandas as pd
from my_functions import cleaned_data, feature

def test_cleaned_data():
    """Test data cleaning."""
    raw = pd.DataFrame({
        'col_a': [1, 2, None, 4],
        'col_b': ['a', 'b', 'c', 'd']
    })
    result = cleaned_data(raw)
    assert len(result) == 3
    assert result['col_a'].isna().sum() == 0

def test_feature():
    """Test feature calculation."""
    data = pd.DataFrame({'col_a': [1, 2, 3]})
    result = feature(data)
    pd.testing.assert_series_equal(
        result,
        pd.Series([2, 4, 6], name='col_a')
    )
```

**Integration Testing with Driver:**
```python
def test_full_pipeline():
    """Test complete DAG execution."""
    from hamilton import driver
    import my_functions

    dr = driver.Driver({}, my_functions)
    result = dr.execute(
        ['result'],
        inputs={'data_path': 'test_data.csv'}
    )
    assert 'result' in result
    assert result['result'].sum() > 0
```

## Common Pitfalls & Solutions

**Circular Dependencies:**
```python
# ❌ Bad - circular dependency
def a(b: int) -> int:
    return b + 1

def b(a: int) -> int:
    return a + 1

# ✅ Good - break the cycle
def a(input_value: int) -> int:
    return input_value + 1

def b(a: int) -> int:
    return a + 1
```

**Missing Type Hints:**
```python
# ❌ Bad - no type hints
def process(data):
    return data * 2

# ✅ Good - clear types
def process(data: pd.Series) -> pd.Series:
    return data * 2
```

**Mutating Inputs:**
```python
# ❌ Bad - mutates input
def add_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    df[col_name] = 0  # Modifies original!
    return df

# ✅ Good - returns new object
def add_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    result = df.copy()
    result[col_name] = 0
    return result
```

## Key Files & Locations

- **Core library**: `hamilton/` - Main package code
- **Driver**: `hamilton/driver.py` - Main orchestration class
- **Function modifiers**: `hamilton/function_modifiers/` - Decorators
- **Examples**: `examples/` - Production examples
- **Tests**: `tests/` - Unit and integration tests
- **Docs**: `docs/` - Official documentation

## Getting Help

- **Documentation**: `docs/` directory in repo
- **Examples**: `examples/` directory for patterns
- **Community**: Apache Hamilton Slack, GitHub issues
- **Other Skills**: Use `/hamilton-scale` for async/Spark, `/hamilton-llm` for AI workflows

## Additional Resources

For detailed reference material, see:
- Apache Hamilton official docs at hamilton.apache.org
- Apache Hamilton GitHub repository examples folder
