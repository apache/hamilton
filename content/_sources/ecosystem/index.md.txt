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
# Ecosystem

Welcome to the Apache Hamilton Ecosystem page! This page showcases the integrations, plugins, and external resources available for Apache Hamilton users.

---

## 🚀 Interactive Tutorials
[tryhamilton.dev](https://www.tryhamilton.dev/)

Learn Apache Hamilton concepts through interactive, browser-based tutorials.

---

## Built-in Integrations

Apache Hamilton provides first-class support for many popular data science and engineering tools through built-in plugins and adapters. These integrations are maintained by the Apache Hamilton community and included in the core project.

### Data Frameworks

Apache Hamilton integrates seamlessly with popular data manipulation libraries:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/pandas.svg" width="20" height="20" style="vertical-align: middle;"> **pandas** | DataFrame operations and transformations | [Examples](https://github.com/apache/hamilton/tree/main/examples/pandas) \| [ResultBuilder](../reference/result-builders/Pandas.rst) |
| <img src="../_static/logos/polars.svg" width="20" height="20" style="vertical-align: middle;"> **Polars** | High-performance DataFrame library | [Examples](https://github.com/apache/hamilton/tree/main/examples/polars) \| [ResultBuilder](../reference/result-builders/Polars.rst) |
| <img src="../_static/logos/pyspark.svg" width="20" height="20" style="vertical-align: middle;"> **PySpark** | Distributed data processing with Spark | [Examples](https://github.com/apache/hamilton/tree/main/examples/spark) \| [GraphAdapter](../reference/graph-adapters/index.rst) |
| <img src="../_static/logos/dask.svg" width="20" height="20" style="vertical-align: middle;"> **Dask** | Parallel computing and distributed arrays | [Examples](https://github.com/apache/hamilton/tree/main/examples/dask) \| [GraphAdapter](../reference/graph-adapters/DaskGraphAdapter.rst) |
| <img src="../_static/logos/ray.svg" width="20" height="20" style="vertical-align: middle;"> **Ray** | Distributed computing framework | [Examples](https://github.com/apache/hamilton/tree/main/examples/ray) \| [GraphAdapter](../reference/graph-adapters/RayGraphAdapter.rst) |
| <img src="../_static/logos/ibis.png" width="20" height="20" style="vertical-align: middle;"> **Ibis** | Portable DataFrame API across backends | [Integration Guide](../integrations/ibis/index.md) |
| <img src="../_static/logos/vaex.png" width="20" height="20" style="vertical-align: middle;"> **Vaex** | Out-of-core DataFrame library | [Examples](https://github.com/apache/hamilton/tree/main/examples/vaex) |
| <img src="../_static/logos/narwhals.png" width="20" height="20" style="vertical-align: middle;"> **Narwhals** | DataFrame-agnostic interface | [Examples](https://github.com/apache/hamilton/tree/main/examples/narwhals) \| [Lifecycle Hook](../reference/lifecycle-hooks/Narwhals.rst) |
| <img src="../_static/logos/numpy.svg" width="20" height="20" style="vertical-align: middle;"> **NumPy** | Numerical computing arrays | [ResultBuilder](../reference/result-builders/Numpy.rst) |
| <img src="../_static/logos/pyarrow.png" width="20" height="20" style="vertical-align: middle;"> **PyArrow** | Columnar in-memory data | [ResultBuilder](../reference/result-builders/PyArrow.rst) |

### Machine Learning & Data Science

Build and deploy ML workflows with Apache Hamilton:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/mlflow.png" width="20" height="20" style="vertical-align: middle;"> **MLflow** | Experiment tracking and model registry | [Examples](https://github.com/apache/hamilton/tree/main/examples/mlflow) \| [Lifecycle Hook](../reference/lifecycle-hooks/MLFlowTracker.rst) |
| <img src="../_static/logos/scikit-learn.png" width="20" height="20" style="vertical-align: middle;"> **scikit-learn** | Machine learning algorithms | [Examples](https://github.com/apache/hamilton/tree/main/examples/scikit-learn) |
| <img src="../_static/logos/xgboost.png" width="20" height="20" style="vertical-align: middle;"> **XGBoost** | Gradient boosting framework | [IO Adapters](../reference/io/available-data-adapters.rst) |
| <img src="../_static/logos/lightgbm.svg" width="20" height="20" style="vertical-align: middle;"> **LightGBM** | Gradient boosting framework | [IO Adapters](../reference/io/available-data-adapters.rst) |
| <img src="../_static/logos/huggingface.svg" width="20" height="20" style="vertical-align: middle;"> **Hugging Face** | Transformers and NLP models | [IO Adapters](../reference/io/available-data-adapters.rst) |
| <img src="../_static/logos/pandera.png" width="20" height="20" style="vertical-align: middle;"> **Pandera** | DataFrame validation | [Examples](https://github.com/apache/hamilton/tree/main/examples/data_quality/pandera) |
| <img src="../_static/logos/pydantic.svg" width="20" height="20" style="vertical-align: middle;"> **Pydantic** | Data validation and settings | [Decorator](../reference/decorators/check_output.rst) |

### Orchestration & Workflow Systems

Use Apache Hamilton within your existing orchestration infrastructure:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/airflow.png" width="20" height="20" style="vertical-align: middle;"> **Airflow** | Workflow orchestration platform | [Examples](https://github.com/apache/hamilton/tree/main/examples/airflow) |
| <img src="../_static/logos/dagster.png" width="20" height="20" style="vertical-align: middle;"> **Dagster** | Data orchestrator | [Examples](https://github.com/apache/hamilton/tree/main/examples/dagster) |
| <img src="../_static/logos/prefect.png" width="20" height="20" style="vertical-align: middle;"> **Prefect** | Workflow orchestration | [Examples](https://github.com/apache/hamilton/tree/main/examples/prefect) |
| <img src="../_static/logos/kedro.png" width="20" height="20" style="vertical-align: middle;"> **Kedro** | Data science pipelines | [Examples](https://github.com/apache/hamilton/tree/main/examples/kedro) |
| <img src="../_static/logos/metaflow.png" width="20" height="20" style="vertical-align: middle;"> **Metaflow** | ML infrastructure | [Integration](https://github.com/outerbounds/hamilton-metaflow) |
| <img src="../_static/logos/dbt.png" width="20" height="20" style="vertical-align: middle;"> **dbt** | Data transformation tool | [Integration Guide](../integrations/dbt.rst) |

### Data Engineering & ETL

Tools for building robust data pipelines:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/dlt.svg" width="20" height="20" style="vertical-align: middle;"> **dlt** | Data loading and transformation | [Integration Guide](../integrations/dlt/index.md) |
| <img src="../_static/logos/feast.png" width="20" height="20" style="vertical-align: middle;"> **Feast** | Feature store | [Examples](https://github.com/apache/hamilton/tree/main/examples/feast) |
| <img src="../_static/logos/fastapi.svg" width="20" height="20" style="vertical-align: middle;"> **FastAPI** | Web service framework | [Integration Guide](../integrations/fastapi.md) |
| <img src="../_static/logos/streamlit.png" width="20" height="20" style="vertical-align: middle;"> **Streamlit** | Interactive web applications | [Integration Guide](../integrations/streamlit.md) |

### Observability & Monitoring

Track and monitor your Apache Hamilton dataflows:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/datadog.png" width="20" height="20" style="vertical-align: middle;"> **Datadog** | Monitoring and analytics | [Lifecycle Hook](../reference/lifecycle-hooks/DDOGTracer.rst) |
| <img src="../_static/logos/opentelemetry.png" width="20" height="20" style="vertical-align: middle;"> **OpenTelemetry** | Observability framework | [Examples](https://github.com/apache/hamilton/tree/main/examples/opentelemetry) |
| <img src="../_static/logos/openlineage.svg" width="20" height="20" style="vertical-align: middle;"> **OpenLineage** | Data lineage tracking | [Examples](https://github.com/apache/hamilton/tree/main/examples/openlineage) \| [Lifecycle Hook](../reference/lifecycle-hooks/OpenLineageAdapter.rst) |
| **Hamilton UI** | Built-in execution tracking | [UI Guide](../hamilton-ui/index.rst) |
| **Experiment Manager** | Lightweight experiment tracking | [Examples](https://github.com/apache/hamilton/tree/main/examples/experiment_management) |

### Visualization

Create visualizations from your dataflows:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/plotly.png" width="20" height="20" style="vertical-align: middle;"> **Plotly** | Interactive plotting | [Examples](https://github.com/apache/hamilton/tree/main/examples/plotly) |
| <img src="../_static/logos/matplotlib.png" width="20" height="20" style="vertical-align: middle;"> **Matplotlib** | Static plotting | [IO Adapters](../reference/io/available-data-adapters.rst) |
| <img src="../_static/logos/rich.svg" width="20" height="20" style="vertical-align: middle;"> **Rich** | Terminal formatting and progress | [Lifecycle Hook](../reference/lifecycle-hooks/RichProgressBar.rst) |

### Developer Tools

Improve your development workflow:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/jupyter.png" width="20" height="20" style="vertical-align: middle;"> **Jupyter** | Notebook magic commands | [Examples](https://github.com/apache/hamilton/tree/main/examples/jupyter_notebook_magic) |
| <img src="../_static/logos/vscode.png" width="20" height="20" style="vertical-align: middle;"> **VS Code** | Language server and extension | [VS Code Guide](../hamilton-vscode/index.rst) |
| <img src="../_static/logos/tqdm.png" width="20" height="20" style="vertical-align: middle;"> **tqdm** | Progress bars | [Lifecycle Hook](../reference/lifecycle-hooks/ProgressBar.rst) |

### Cloud Providers & Infrastructure

Deploy Apache Hamilton to the cloud:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/aws.svg" width="20" height="20" style="vertical-align: middle;"> **AWS** | Amazon Web Services | [Examples](https://github.com/apache/hamilton/tree/main/examples/aws) |
| <img src="../_static/logos/gcp.svg" width="20" height="20" style="vertical-align: middle;"> **Google Cloud** | Google Cloud Platform | [Scale-up Guide](../how-tos/scale-up.rst) |
| <img src="../_static/logos/modal.png" width="20" height="20" style="vertical-align: middle;"> **Modal** | Serverless cloud functions | [Scale-up Guide](../how-tos/scale-up.rst) |

### Storage & Caching

Persist and cache your data:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/diskcache.png" width="20" height="20" style="vertical-align: middle;"> **DiskCache** | Disk-based caching | [Examples](https://github.com/apache/hamilton/tree/main/examples/caching_nodes/diskcache_adapter) |
| **File-based caching** | Local file caching | [Caching Guide](../reference/caching/index.rst) |

### Other Utilities

| Integration | Description | Documentation |
|------------|-------------|---------------|
| <img src="../_static/logos/slack.svg" width="20" height="20" style="vertical-align: middle;"> **Slack** | Notifications and integrations | [Examples](https://github.com/apache/hamilton/tree/main/examples/slack) \| [Lifecycle Hook](../reference/lifecycle-hooks/SlackNotifierHook.rst) |
| <img src="../_static/logos/geopandas.png" width="20" height="20" style="vertical-align: middle;"> **GeoPandas** | Geospatial data analysis | [Type extension](https://github.com/apache/hamilton/blob/main/hamilton/plugins/geopandas_extensions.py) for GeoDataFrame support |
| <img src="../_static/logos/yaml.svg" width="20" height="20" style="vertical-align: middle;"> **YAML** | Configuration management | [IO Adapters](../reference/io/available-data-adapters.rst) |

---

## External Resources

The following resources and services are provided by third parties and the broader Apache Hamilton community.

**⚠️ Important Notice:**

These resources and services are **not maintained, nor endorsed** by the Apache Hamilton Community and Apache Hamilton project (maintained by the Committers and the Apache Hamilton PMC). Use them at your sole discretion. The community does not verify the licenses nor validity of these tools, so it's your responsibility to verify them.

### Community Resources

#### 📚 Dataflow Hub
[hub.dagworks.io](https://hub.dagworks.io/docs/)

A repository of reusable Apache Hamilton dataflows contributed by the community. Browse and download pre-built dataflows for common use cases.

**Note**: It's WIP to move the domain to be under Apache. DAGWorks Inc., which donated Hamilton, is not an operating entity anymore.

#### 📝 Blog & Tutorials
[blog.dagworks.io](https://blog.dagworks.io/)

Articles covering Apache Hamilton use cases, design patterns, reference architectures, and best practices.

**Note**: It's WIP to move the contents to be under Apache. DAGWorks Inc., which donated Hamilton, is not an operating entity anymore.

#### 🎥 Video Content
[YouTube @DAGWorks-Inc](https://www.youtube.com/@DAGWorks-Inc)

Video tutorials, talks, and meetup recordings about Apache Hamilton.

**Note**: It's WIP to move the contents to be under Apache. DAGWorks Inc., which donated Hamilton, is not an operating entity anymore.



---

## Contributing to the Ecosystem

### Adding a New Integration

If you've created a plugin or integration for Apache Hamilton, we'd love to include it in our ecosystem!

**For Built-in Integrations** (maintained by the Apache Hamilton project):
1. Create a plugin in the `hamilton/plugins/` directory
2. Add documentation and examples
3. Submit a pull request to the [Apache Hamilton repository](https://github.com/apache/hamilton)
4. Follow the [contribution guidelines](https://github.com/apache/hamilton/blob/main/CONTRIBUTING.md)

**For External Resources** (maintained by third parties):
1. Submit a pull request to add your resource to this page under "External Resources"
2. Include a clear description and link
3. Ensure your resource is relevant to Apache Hamilton users
4. Your resource must be properly licensed and actively maintained

### Support & Questions

- 💬 [Slack Community](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g) - Real-time chat and community support
- 🐛 [GitHub Issues](https://github.com/apache/hamilton/issues) - Bug reports and feature requests
- 📖 [Documentation](https://hamilton.apache.org) - Comprehensive guides and API reference
- 📧 **Mailing List** - Join the Apache Hamilton users mailing list for discussions and announcements
  - **How to Subscribe**: Send an empty email to [users-subscribe@hamilton.apache.org](mailto:users-subscribe@hamilton.apache.org). Use a subject line like "subscribe" to avoid spam filters. Await a confirmation message and follow the instructions to complete the process.
  - **How to Unsubscribe**: Send an empty message to [users-unsubscribe@hamilton.apache.org](mailto:users-unsubscribe@hamilton.apache.org) from the same email address used to subscribe.
  - **How to Post**: Once subscribed, post messages to [users@hamilton.apache.org](mailto:users@hamilton.apache.org)
  - **Archives**: [View past discussions](https://lists.apache.org/list.html?users@hamilton.apache.org)

---

## Stay Updated

- ⭐ Star us on [GitHub](https://github.com/apache/hamilton)
- 🐦 Follow [@hamilton_os](https://twitter.com/hamilton_os) on Twitter/X
- 📧 Join the [mailing lists](../asf/index.rst) for announcements
