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
name: hamilton-integrations
description: Hamilton integration patterns for Airflow, Dagster, FastAPI, Streamlit, Jupyter notebooks, and other frameworks. Use when integrating Hamilton with other tools.
allowed-tools: Read, Grep, Glob, Bash(python:*), Bash(jupyter:*)
user-invocable: true
disable-model-invocation: false
---

# Hamilton Integrations

This skill covers integrating Hamilton with orchestrators, web frameworks, notebooks, and other tools.

## Why Integrate Hamilton?

Hamilton focuses on **dataflow definition**, letting you integrate with:
- **Orchestrators** (Airflow, Dagster, Prefect) - Schedule and monitor
- **Web frameworks** (FastAPI, Flask) - Serve predictions
- **Dashboards** (Streamlit, Plotly Dash) - Interactive visualization
- **Notebooks** (Jupyter) - Interactive development
- **Experiment tracking** (MLflow, Weights & Biases) - Track experiments

## Airflow Integration

**Use Case:** Schedule Hamilton DAGs as Airflow tasks

```python
"""Hamilton in Airflow DAG."""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from hamilton import driver
import my_hamilton_module

def run_hamilton_pipeline(**context):
    """Execute Hamilton DAG within Airflow task."""
    dr = driver.Driver({}, my_hamilton_module)

    results = dr.execute(
        ['final_output'],
        inputs={
            'data_date': context['ds'],  # Airflow execution date
            'run_id': context['run_id']
        }
    )

    # Push results to XCom for downstream tasks
    context['task_instance'].xcom_push(key='results', value=results)
    return results

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
    'hamilton_etl_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:

    hamilton_task = PythonOperator(
        task_id='run_hamilton_etl',
        python_callable=run_hamilton_pipeline,
        provide_context=True
    )
```

**Multiple Hamilton DAGs in Airflow:**

```python
"""Orchestrate multiple Hamilton pipelines."""
def run_data_ingestion(**context):
    """Hamilton pipeline 1: Ingest data."""
    import ingestion_module
    dr = driver.Driver({}, ingestion_module)
    return dr.execute(['ingested_data'], inputs={'date': context['ds']})

def run_feature_engineering(**context):
    """Hamilton pipeline 2: Feature engineering."""
    import feature_module
    # Get data from previous task
    ingested_data = context['task_instance'].xcom_pull(task_ids='ingest')
    dr = driver.Driver({}, feature_module)
    return dr.execute(['features'], inputs={'raw_data': ingested_data})

def run_model_training(**context):
    """Hamilton pipeline 3: Train model."""
    import training_module
    features = context['task_instance'].xcom_pull(task_ids='features')
    dr = driver.Driver({}, training_module)
    return dr.execute(['trained_model'], inputs={'features': features})

with DAG('ml_pipeline', schedule_interval='@weekly') as dag:
    ingest = PythonOperator(task_id='ingest', python_callable=run_data_ingestion)
    features = PythonOperator(task_id='features', python_callable=run_feature_engineering)
    train = PythonOperator(task_id='train', python_callable=run_model_training)

    ingest >> features >> train
```

## Dagster Integration

**Use Case:** Define Hamilton as Dagster assets

```python
"""Hamilton in Dagster."""
from dagster import asset, AssetExecutionContext
from hamilton import driver
import my_hamilton_module

@asset
def customer_features(context: AssetExecutionContext) -> dict:
    """Execute Hamilton DAG as Dagster asset."""
    dr = driver.Driver({}, my_hamilton_module)

    context.log.info("Starting Hamilton pipeline")

    results = dr.execute(
        ['customer_segments', 'feature_importance'],
        inputs={'data_path': '/data/customers.csv'}
    )

    context.log.info(f"Generated {len(results['customer_segments'])} segments")

    return results

@asset(deps=[customer_features])
def segment_report(context: AssetExecutionContext, customer_features: dict) -> str:
    """Use Hamilton output in downstream Dagster asset."""
    segments = customer_features['customer_segments']
    # Generate report
    return f"Processed {len(segments)} segments"
```

## FastAPI Integration

**Use Case:** Serve Hamilton DAGs as REST API endpoints

```python
"""Hamilton as FastAPI microservice."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from hamilton import driver
import prediction_module

app = FastAPI(title="ML Prediction Service")

# Initialize driver once at startup
prediction_driver = driver.Driver({}, prediction_module)

class PredictionRequest(BaseModel):
    """Request schema."""
    user_id: str
    feature_a: float
    feature_b: float
    feature_c: float

class PredictionResponse(BaseModel):
    """Response schema."""
    user_id: str
    prediction: float
    confidence: float

@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    """Stateless prediction endpoint."""
    try:
        result = prediction_driver.execute(
            ['prediction', 'confidence'],
            inputs=request.dict()
        )

        return PredictionResponse(
            user_id=request.user_id,
            prediction=result['prediction'],
            confidence=result['confidence']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "hamilton-predictor"}

# Run with: uvicorn main:app --reload
```

**Async FastAPI with Async Hamilton:**

```python
"""Async Hamilton with FastAPI."""
from fastapi import FastAPI
from hamilton import async_driver
import async_prediction_module

app = FastAPI()

# Async driver initialization
prediction_driver = None

@app.on_event("startup")
async def startup():
    """Initialize async driver on startup."""
    global prediction_driver
    prediction_driver = await async_driver.Builder()\
        .with_modules(async_prediction_module)\
        .build()

@app.post("/predict")
async def predict(request: PredictionRequest):
    """Async prediction endpoint."""
    result = await prediction_driver.execute(
        ['prediction'],
        inputs=request.dict()
    )
    return {"prediction": result['prediction']}
```

## Streamlit Integration

**Use Case:** Interactive data apps with Hamilton

```python
"""Hamilton-powered Streamlit dashboard."""
import streamlit as st
from hamilton import driver
import analytics_module

st.title("Customer Analytics Dashboard")

# Sidebar controls
date_range = st.sidebar.date_input("Select date range", [])
metric = st.sidebar.selectbox("Metric", ["revenue", "users", "conversions"])
segment = st.sidebar.multiselect("Segments", ["new", "returning", "churned"])

# Execute Hamilton DAG with user inputs
if st.sidebar.button("Run Analysis"):
    with st.spinner("Running analysis..."):
        dr = driver.Driver({'metric': metric}, analytics_module)

        results = dr.execute(
            ['daily_metrics', 'segment_breakdown', 'trends'],
            inputs={
                'date_range': date_range,
                'segments': segment
            }
        )

        # Display results
        st.header("Daily Metrics")
        st.line_chart(results['daily_metrics'])

        st.header("Segment Breakdown")
        st.bar_chart(results['segment_breakdown'])

        st.header("Trends")
        st.dataframe(results['trends'])

        # Visualize DAG
        st.header("Pipeline Visualization")
        dr.visualize_execution(
            ['trends'],
            './pipeline.png',
            inputs={'date_range': date_range, 'segments': segment}
        )
        st.image('./pipeline.png')
```

## Jupyter Notebook Integration

**Use Case:** Interactive development and experimentation

### Jupyter Magic Extension

```python
"""Use Hamilton directly in notebooks."""
# Install magic extension
%load_ext hamilton.plugins.jupyter_magic

# Define Hamilton functions in cells
%%cell_to_module my_analysis --display

import pandas as pd

def raw_data(csv_path: str) -> pd.DataFrame:
    """Load data."""
    return pd.read_csv(csv_path)

def cleaned_data(raw_data: pd.DataFrame) -> pd.DataFrame:
    """Clean data."""
    return raw_data.dropna()

def summary_stats(cleaned_data: pd.DataFrame) -> dict:
    """Calculate summary."""
    return {
        'mean': cleaned_data['value'].mean(),
        'std': cleaned_data['value'].std()
    }

# Displays DAG visualization automatically!
```

### Standard Notebook Pattern

```python
"""Hamilton in Jupyter without magic."""
# Cell 1: Define Hamilton functions
# my_functions.py equivalent
def load_data(data_path: str) -> pd.DataFrame:
    return pd.read_csv(data_path)

def process_data(load_data: pd.DataFrame) -> pd.DataFrame:
    return load_data.dropna()

# Cell 2: Create driver
from hamilton import driver
import sys

# Add current module to driver
dr = driver.Driver({}, sys.modules[__name__])

# Cell 3: Execute and explore
results = dr.execute(
    ['process_data'],
    inputs={'data_path': 'data.csv'}
)

results['process_data'].head()

# Cell 4: Visualize
dr.visualize_execution(
    ['process_data'],
    './notebook_dag.png',
    inputs={'data_path': 'data.csv'}
)

from IPython.display import Image
Image('./notebook_dag.png')
```

## MLflow Integration

**Use Case:** Track experiments and models

```python
"""Hamilton with MLflow tracking."""
from hamilton import driver
from hamilton.plugins.mlflow_extensions import MLFlowTracker
import mlflow
import training_module

# Configure MLflow
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("customer_churn")

with mlflow.start_run():
    # Create MLflow adapter
    mlflow_tracker = MLFlowTracker(
        experiment_name="customer_churn",
        run_name="baseline_model_v1",
        tags={"model_type": "random_forest", "version": "1.0"}
    )

    # Hamilton driver with MLflow tracking
    dr = driver.Builder()\
        .with_config({'model_type': 'random_forest'})\
        .with_modules(training_module)\
        .with_adapters(mlflow_tracker)\
        .build()

    results = dr.execute(
        ['trained_model', 'metrics'],
        inputs={'training_data': train_df}
    )

    # Log additional metrics
    mlflow.log_metrics(results['metrics'])
    mlflow.log_param("features_count", len(results['features']))
```

## Weights & Biases Integration

```python
"""Hamilton with W&B tracking."""
import wandb
from hamilton import driver
import experiment_module

# Initialize W&B
wandb.init(project="ml-experiments", name="experiment-42")

# Configure Hamilton
config = {
    'learning_rate': 0.001,
    'batch_size': 32,
    'epochs': 10
}

# Log config to W&B
wandb.config.update(config)

dr = driver.Driver(config, experiment_module)

results = dr.execute(
    ['trained_model', 'validation_metrics'],
    inputs={'data_path': '/data/train.csv'}
)

# Log results to W&B
wandb.log({
    "val_accuracy": results['validation_metrics']['accuracy'],
    "val_loss": results['validation_metrics']['loss']
})

wandb.finish()
```

## Flask Integration

```python
"""Hamilton with Flask."""
from flask import Flask, request, jsonify
from hamilton import driver
import service_module

app = Flask(__name__)
service_driver = driver.Driver({}, service_module)

@app.route('/api/process', methods=['POST'])
def process_data():
    """Process data endpoint."""
    data = request.get_json()

    try:
        results = service_driver.execute(
            ['processed_result'],
            inputs=data
        )
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

## dbt Integration

**Use Case:** Hamilton for transformations, dbt for SQL

```python
"""Hamilton after dbt transformations."""
import subprocess
from hamilton import driver
import post_dbt_module

def run_dbt() -> dict:
    """Run dbt pipeline."""
    result = subprocess.run(['dbt', 'run'], capture_output=True)
    return {'status': 'success' if result.returncode == 0 else 'failed'}

def dbt_output_path(run_dbt: dict) -> str:
    """Get dbt output location."""
    return './target/output.csv'

# Rest of Hamilton DAG uses dbt output
def post_dbt_analysis(dbt_output_path: str) -> pd.DataFrame:
    """Analyze dbt output."""
    return pd.read_csv(dbt_output_path)
```

## Kedro Integration

```python
"""Use Hamilton within Kedro pipelines."""
from kedro.pipeline import Pipeline, node
from hamilton import driver
import hamilton_transformations

def run_hamilton_node(**inputs):
    """Execute Hamilton as Kedro node."""
    dr = driver.Driver({}, hamilton_transformations)
    return dr.execute(['output'], inputs=inputs)

def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline([
        node(
            func=run_hamilton_node,
            inputs=["raw_data", "parameters"],
            outputs="hamilton_results",
            name="hamilton_transformation"
        )
    ])
```

## Best Practices

1. **Initialize driver once** - Reuse driver across requests in web services
2. **Separate concerns** - Orchestrator handles scheduling, Hamilton handles dataflow
3. **Use async** - FastAPI + async Hamilton for I/O-bound workflows
4. **Track everywhere** - Add HamiltonTracker to production integrations
5. **Health checks** - Expose health endpoints for monitoring
6. **Error handling** - Wrap Hamilton execution in try/except
7. **Configuration** - Pass environment-specific config to Hamilton

## Choosing the Right Integration

| Use Case | Tool | When to Use |
|----------|------|-------------|
| Schedule pipelines | Airflow, Dagster | Daily/weekly batch processing |
| Serve predictions | FastAPI, Flask | Real-time ML inference |
| Interactive dashboards | Streamlit | Business intelligence, exploration |
| Development | Jupyter | Prototyping, analysis |
| Experiment tracking | MLflow, W&B | ML model development |
| SQL + Python | dbt | Most data in warehouse, some Python logic |

## Additional Resources

- For core Hamilton patterns, use `/hamilton-core`
- For observability, use `/hamilton-observability`
- Examples: github.com/apache/hamilton/tree/main/examples
