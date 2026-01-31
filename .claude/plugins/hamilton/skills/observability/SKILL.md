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
name: hamilton-observability
description: Hamilton UI and SDK patterns for tracking, monitoring, and debugging dataflows. Use for observability, lineage tracking, and production monitoring.
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(hamilton:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton Observability & UI

This skill covers the Hamilton UI, SDK, and observability patterns for tracking and monitoring your dataflows in development and production.

## What is Hamilton UI?

Hamilton UI is a web-based dashboard for:
- **Tracking DAG executions** - See every run with inputs, outputs, and timing
- **Visualizing dataflows** - Interactive DAG visualization
- **Debugging failures** - Inspect errors and intermediate values
- **Lineage tracking** - Understand data provenance
- **Performance monitoring** - Identify bottlenecks
- **Team collaboration** - Share DAGs and results

## Quick Start

### 1. Install Hamilton with UI Support

```bash
pip install "sf-hamilton[sdk,ui]"
```

### 2. Start the Hamilton UI

```bash
# Start the UI server locally
hamilton ui

# UI will be available at http://localhost:8241
```

### 3. Add Tracking to Your Code

```python
"""Add HamiltonTracker to your driver."""
from hamilton_sdk import adapters
from hamilton import driver

# Create tracker
tracker = adapters.HamiltonTracker(
    project_id=1,  # Your project ID from UI
    username="your.email@example.com",
    dag_name="my_pipeline",
    tags={"environment": "dev", "team": "data-science"}
)

# Build driver with tracker
dr = driver.Builder()\
    .with_config(your_config)\
    .with_modules(*your_modules)\
    .with_adapters(tracker)\
    .build()

# Execute as normal - runs are automatically tracked!
results = dr.execute(['final_output'], inputs={'data_path': 'data.csv'})
```

### 4. View in UI

Open http://localhost:8241 and see:
- Your DAG visualization
- Execution history
- Node-level timing
- Input/output values

## HamiltonTracker Features

### Basic Tracking

```python
"""Minimal tracking setup."""
from hamilton_sdk import adapters

tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="etl_pipeline"
)

# Attach to driver
dr = driver.Builder().with_adapters(tracker).build()
```

### Advanced Tracking with Tags

```python
"""Use tags for filtering and organization."""
tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="ml_training",
    tags={
        "environment": "production",
        "model_version": "v2.1",
        "team": "ml-platform",
        "experiment_id": "exp_123"
    }
)

# Tags appear in UI for filtering and search
```

### Async Tracking

```python
"""Track async workflows."""
from hamilton import async_driver
from hamilton_sdk import adapters

tracker = adapters.AsyncHamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="async_rag_pipeline"
)

dr = await async_driver.Builder()\
    .with_modules(async_module)\
    .with_adapters(tracker)\
    .build()

result = await dr.execute(['llm_response'], inputs={'query': 'test'})
```

## Project Organization

### Creating Projects

Projects group related DAGs together:

```bash
# Create project via UI
# 1. Open http://localhost:8241
# 2. Click "New Project"
# 3. Name it (e.g., "Customer Analytics")
# 4. Get the project_id

# Or via API
import requests
response = requests.post(
    "http://localhost:8241/api/v1/projects",
    json={"name": "Customer Analytics", "description": "Customer data pipelines"}
)
project_id = response.json()['id']
```

### Organizing by Team

```python
"""Organize DAGs by team and environment."""
# Team A - Development
tracker_team_a_dev = adapters.HamiltonTracker(
    project_id=1,  # "Team A Analytics" project
    username="user@example.com",
    dag_name="user_segmentation",
    tags={"team": "team-a", "env": "dev"}
)

# Team A - Production
tracker_team_a_prod = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="user_segmentation",
    tags={"team": "team-a", "env": "prod"}
)

# Team B - Different project
tracker_team_b = adapters.HamiltonTracker(
    project_id=2,  # "Team B ML" project
    username="user@example.com",
    dag_name="recommendation_model",
    tags={"team": "team-b", "env": "dev"}
)
```

## Debugging with Hamilton UI

### Inspecting Failed Runs

When a DAG fails, the UI shows:
1. **Which node failed** - Visual highlighting
2. **Error message** - Full stack trace
3. **Inputs to failed node** - Inspect what caused the failure
4. **Successful nodes** - What completed before failure
5. **Timing** - Where time was spent before failure

```python
"""DAG fails at 'processed_data' node."""
# In UI:
# - Navigate to failed run
# - Click on red 'processed_data' node
# - See error: "ValueError: Cannot convert string to float"
# - Inspect inputs: raw_data contains 'N/A' strings
# - Fix data cleaning logic
```

### Comparing Runs

Compare two DAG runs side-by-side:
- Input differences
- Timing changes
- Output value changes
- Code changes

```python
"""Compare dev vs prod performance."""
# Run 1: Development (10 seconds)
# Run 2: Production (45 seconds)

# In UI:
# - Select both runs
# - Click "Compare"
# - See: 'feature_engineering' node is 8x slower in prod
# - Reason: Prod has 10x more data
# - Solution: Add caching or parallelize
```

### Node-Level Inspection

Drill into any node to see:
- Execution time
- Input values
- Output values (if stored)
- Error details (if failed)
- Code version

## Lineage Tracking

### Understanding Data Provenance

Hamilton UI automatically tracks:
- **Upstream dependencies** - What data contributed to this result?
- **Downstream impact** - What depends on this node?
- **Cross-DAG lineage** - Track data between different pipelines

```python
"""Track lineage across training and inference."""
# Training pipeline
training_tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="model_training",
    tags={"stage": "training", "model_version": "v2.1"}
)

# Inference pipeline (same project)
inference_tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="model_inference",
    tags={"stage": "inference", "model_version": "v2.1"}
)

# In UI: Filter by model_version="v2.1" to see both pipelines
```

## Production Monitoring

### Key Metrics to Track

```python
"""Track production metrics."""
tracker = adapters.HamiltonTracker(
    project_id=1,
    username="service@example.com",
    dag_name="production_etl",
    tags={
        "environment": "production",
        "service": "data-pipeline",
        "version": os.getenv("SERVICE_VERSION", "unknown"),
        "host": os.getenv("HOSTNAME", "unknown")
    }
)

# Monitor in UI:
# - Execution frequency (runs per hour)
# - Success rate (failures per day)
# - Execution time trends
# - Node-level performance
```

### Alerting on Failures

```python
"""Set up failure notifications."""
# Hamilton UI can send alerts on:
# - DAG failures
# - Slow executions (> threshold)
# - Specific node failures

# Configure in UI:
# 1. Go to Project Settings
# 2. Set up webhook or email alerts
# 3. Define alert conditions
```

### Performance Monitoring

Track performance over time:

```python
"""Monitor performance degradation."""
# Week 1: Average execution time = 5 minutes
# Week 2: Average execution time = 8 minutes
# Week 3: Average execution time = 12 minutes

# In UI:
# - View execution time chart
# - Identify 'data_processing' node is slowing down
# - Root cause: Data volume increased 3x
# - Solution: Add partitioning or switch to Spark
```

## Integration with Other Tools

### MLflow Integration

```python
"""Track both Hamilton and MLflow."""
from hamilton_sdk import adapters
import mlflow

hamilton_tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="ml_training"
)

# Use both adapters
dr = driver.Builder()\
    .with_adapters(hamilton_tracker, mlflow_tracker)\
    .build()

# Results tracked in both Hamilton UI and MLflow
```

### Airflow Integration

```python
"""Track Hamilton DAGs in Airflow tasks."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from hamilton_sdk import adapters

def run_hamilton_pipeline(**context):
    """Execute Hamilton with tracking."""
    tracker = adapters.HamiltonTracker(
        project_id=1,
        username="airflow@example.com",
        dag_name="airflow_etl",
        tags={
            "airflow_dag": context['dag'].dag_id,
            "airflow_run": context['run_id'],
            "task": context['task_instance'].task_id
        }
    )

    dr = driver.Builder()\
        .with_modules(my_module)\
        .with_adapters(tracker)\
        .build()

    return dr.execute(['output'], inputs=context['params'])

with DAG('my_dag', schedule_interval='@daily') as dag:
    task = PythonOperator(
        task_id='hamilton_pipeline',
        python_callable=run_hamilton_pipeline
    )
```

## SDK Advanced Usage

### Querying Runs Programmatically

```python
"""Query Hamilton UI via SDK."""
from hamilton_sdk import client

# Connect to Hamilton UI
hc = client.HamiltonClient(
    base_url="http://localhost:8241",
    username="user@example.com"
)

# Get recent runs
runs = hc.get_runs(
    project_id=1,
    dag_name="my_pipeline",
    limit=10
)

for run in runs:
    print(f"Run {run.id}: {run.status} in {run.duration}s")

# Get specific run details
run_detail = hc.get_run(run_id=runs[0].id)
print(f"Inputs: {run_detail.inputs}")
print(f"Outputs: {run_detail.outputs}")
```

### Custom Metadata

```python
"""Add custom metadata to runs."""
tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="my_pipeline",
    tags={
        "git_commit": subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
        "git_branch": subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip(),
        "dataset_version": "v2024.01",
        "experiment_name": "baseline_v2"
    }
)

# All metadata searchable in UI
```

## Best Practices

1. **Use descriptive dag_names** - Make them searchable (e.g., "user_segmentation_daily" not "pipeline_1")
2. **Tag consistently** - Use standard keys (environment, team, version)
3. **Track production** - Always enable tracking in production
4. **Monitor trends** - Set up dashboards for key metrics
5. **Clean up old runs** - Archive or delete runs after retention period
6. **Use projects** - Organize by team/domain, not by environment
7. **Document tags** - Create team standard for tag keys and values

## Troubleshooting

### UI Not Showing Runs

```bash
# Check UI is running
curl http://localhost:8241/api/v1/ping

# Check tracker configuration
tracker = adapters.HamiltonTracker(
    project_id=1,  # Does this project exist?
    username="user@example.com",  # Is this user registered?
    dag_name="my_pipeline",
    api_url="http://localhost:8241"  # Override if UI is on different host
)
```

### Slow UI Performance

```python
"""Optimize tracking for large DAGs."""
tracker = adapters.HamiltonTracker(
    project_id=1,
    username="user@example.com",
    dag_name="large_pipeline",
    # Don't capture large outputs
    capture_data_statistics=False,  # Skip stats collection
    # Or be selective about what to capture
)
```

## Additional Resources

- For core Hamilton patterns, use `/hamilton-core`
- For scaling patterns, use `/hamilton-scale`
- Hamilton UI docs: hamilton.apache.org/concepts/ui
- Hamilton SDK docs: github.com/apache/hamilton/tree/main/ui/sdk
