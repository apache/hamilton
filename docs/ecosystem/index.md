# Ecosystem

Welcome to the Apache Hamilton Ecosystem page! This page showcases the integrations, plugins, and external resources available for Apache Hamilton users.

## Built-in Integrations

Apache Hamilton provides first-class support for many popular data science and engineering tools through built-in plugins and adapters. These integrations are maintained by the Apache Hamilton community and included in the core project.

### Data Frameworks

Apache Hamilton integrates seamlessly with popular data manipulation libraries:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **pandas** | DataFrame operations and transformations | [Examples](https://github.com/apache/hamilton/tree/main/examples/pandas) \| [ResultBuilder](../reference/result-builders/Pandas.rst) |
| **Polars** | High-performance DataFrame library | [Examples](https://github.com/apache/hamilton/tree/main/examples/polars) \| [ResultBuilder](../reference/result-builders/Polars.rst) |
| **PySpark** | Distributed data processing with Spark | [Examples](https://github.com/apache/hamilton/tree/main/examples/spark) \| [GraphAdapter](../reference/graph-adapters/index.rst) |
| **Dask** | Parallel computing and distributed arrays | [Examples](https://github.com/apache/hamilton/tree/main/examples/dask) \| [GraphAdapter](../reference/graph-adapters/DaskGraphAdapter.rst) |
| **Ray** | Distributed computing framework | [Examples](https://github.com/apache/hamilton/tree/main/examples/ray) \| [GraphAdapter](../reference/graph-adapters/RayGraphAdapter.rst) |
| **Ibis** | Portable DataFrame API across backends | [Integration Guide](../integrations/ibis/index.md) |
| **Vaex** | Out-of-core DataFrame library | [Examples](https://github.com/apache/hamilton/tree/main/examples/vaex) |
| **Narwhals** | DataFrame-agnostic interface | [Examples](https://github.com/apache/hamilton/tree/main/examples/narwhals) \| [Lifecycle Hook](../reference/lifecycle-hooks/Narwhals.rst) |
| **NumPy** | Numerical computing arrays | [ResultBuilder](../reference/result-builders/Numpy.rst) |
| **PyArrow** | Columnar in-memory data | [ResultBuilder](../reference/result-builders/PyArrow.rst) |

### Machine Learning & Data Science

Build and deploy ML workflows with Apache Hamilton:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **MLflow** | Experiment tracking and model registry | [Examples](https://github.com/apache/hamilton/tree/main/examples/mlflow) \| [Lifecycle Hook](../reference/lifecycle-hooks/MLFlowTracker.rst) |
| **scikit-learn** | Machine learning algorithms | [Examples](https://github.com/apache/hamilton/tree/main/examples/scikit-learn) |
| **XGBoost** | Gradient boosting framework | [IO Adapters](../reference/io/available-data-adapters.rst) |
| **LightGBM** | Gradient boosting framework | [IO Adapters](../reference/io/available-data-adapters.rst) |
| **Hugging Face** | Transformers and NLP models | [IO Adapters](../reference/io/available-data-adapters.rst) |
| **Pandera** | DataFrame validation | [Examples](https://github.com/apache/hamilton/tree/main/examples/data_quality/pandera) |
| **Pydantic** | Data validation and settings | [Decorator](../reference/decorators/check_output.rst) |

### Orchestration & Workflow Systems

Use Apache Hamilton within your existing orchestration infrastructure:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **Airflow** | Workflow orchestration platform | [Examples](https://github.com/apache/hamilton/tree/main/examples/airflow) |
| **Dagster** | Data orchestrator | [Examples](https://github.com/apache/hamilton/tree/main/examples/dagster) |
| **Prefect** | Workflow orchestration | [Examples](https://github.com/apache/hamilton/tree/main/examples/prefect) |
| **Kedro** | Data science pipelines | [Examples](https://github.com/apache/hamilton/tree/main/examples/kedro) |
| **Metaflow** | ML infrastructure | [Integration](https://github.com/outerbounds/hamilton-metaflow) |
| **dbt** | Data transformation tool | [Integration Guide](../integrations/dbt.rst) |

### Data Engineering & ETL

Tools for building robust data pipelines:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **dlt** | Data loading and transformation | [Integration Guide](../integrations/dlt/index.md) |
| **Feast** | Feature store | [Examples](https://github.com/apache/hamilton/tree/main/examples/feast) |
| **FastAPI** | Web service framework | [Integration Guide](../integrations/fastapi.md) |
| **Streamlit** | Interactive web applications | [Integration Guide](../integrations/streamlit.md) |

### Observability & Monitoring

Track and monitor your Apache Hamilton dataflows:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **Datadog** | Monitoring and analytics | [Lifecycle Hook](../reference/lifecycle-hooks/DDOGTracer.rst) |
| **OpenTelemetry** | Observability framework | [Examples](https://github.com/apache/hamilton/tree/main/examples/opentelemetry) |
| **OpenLineage** | Data lineage tracking | [Examples](https://github.com/apache/hamilton/tree/main/examples/openlineage) \| [Lifecycle Hook](../reference/lifecycle-hooks/OpenLineageAdapter.rst) |
| **Hamilton UI** | Built-in execution tracking | [UI Guide](../hamilton-ui/index.rst) |
| **Experiment Manager** | Lightweight experiment tracking | [Examples](https://github.com/apache/hamilton/tree/main/examples/experiment_management) |

### Visualization

Create visualizations from your dataflows:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **Plotly** | Interactive plotting | [Examples](https://github.com/apache/hamilton/tree/main/examples/plotly) |
| **Matplotlib** | Static plotting | [IO Adapters](../reference/io/available-data-adapters.rst) |
| **Rich** | Terminal formatting and progress | [Lifecycle Hook](../reference/lifecycle-hooks/RichProgressBar.rst) |

### Developer Tools

Improve your development workflow:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **Jupyter** | Notebook magic commands | [Examples](https://github.com/apache/hamilton/tree/main/examples/jupyter_notebook_magic) |
| **VS Code** | Language server and extension | [VS Code Guide](../hamilton-vscode/index.rst) |
| **tqdm** | Progress bars | [Lifecycle Hook](../reference/lifecycle-hooks/ProgressBar.rst) |

### Cloud Providers & Infrastructure

Deploy Apache Hamilton to the cloud:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **AWS** | Amazon Web Services | [Examples](https://github.com/apache/hamilton/tree/main/examples/aws) |
| **Google Cloud** | Google Cloud Platform | [Scale-up Guide](../how-tos/scale-up.rst) |
| **Modal** | Serverless cloud functions | [Scale-up Guide](../how-tos/scale-up.rst) |

### Storage & Caching

Persist and cache your data:

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **DiskCache** | Disk-based caching | [Examples](https://github.com/apache/hamilton/tree/main/examples/caching_nodes/diskcache_adapter) |
| **File-based caching** | Local file caching | [Caching Guide](../reference/caching/index.rst) |

### Other Utilities

| Integration | Description | Documentation |
|------------|-------------|---------------|
| **Slack** | Notifications and integrations | [Examples](https://github.com/apache/hamilton/tree/main/examples/slack) \| [Lifecycle Hook](../reference/lifecycle-hooks/SlackNotifierHook.rst) |
| **GeoPandas** | Geospatial data analysis | Type extension for GeoDataFrame support |
| **YAML** | Configuration management | [IO Adapters](../reference/io/available-data-adapters.rst) |

---

## External Resources

The following resources and services are provided by third parties and the broader Apache Hamilton community.

**⚠️ Important Notice:**

These resources and services are **not maintained, nor endorsed** by the Apache Hamilton Community and Apache Hamilton project (maintained by the Committers and the Apache Hamilton PMC). Use them at your sole discretion. The community does not verify the licenses nor validity of these tools, so it's your responsibility to verify them.

### Community Resources

#### 📚 Dataflow Hub
[hub.dagworks.io](https://hub.dagworks.io/docs/)

A repository of reusable Apache Hamilton dataflows contributed by the community. Browse and download pre-built dataflows for common use cases.

**Note**: Hosted by DAGWorks Inc., a company founded by Apache Hamilton's original creators.

#### 📝 Blog & Tutorials
[blog.dagworks.io](https://blog.dagworks.io/)

Articles covering Apache Hamilton use cases, design patterns, reference architectures, and best practices.

**Note**: Maintained by DAGWorks Inc.

#### 🎥 Video Content
[YouTube @DAGWorks-Inc](https://www.youtube.com/@DAGWorks-Inc)

Video tutorials, talks, and meetup recordings about Apache Hamilton.

**Note**: Hosted by DAGWorks Inc.

#### 🚀 Interactive Tutorials
[tryhamilton.dev](https://www.tryhamilton.dev/)

Learn Apache Hamilton concepts through interactive, browser-based tutorials.

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

- 💬 [Slack Community](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g)
- 🐛 [GitHub Issues](https://github.com/apache/hamilton/issues)
- 📖 [Documentation](https://hamilton.apache.org)

---

## Stay Updated

- ⭐ Star us on [GitHub](https://github.com/apache/hamilton)
- 🐦 Follow [@hamilton_os](https://twitter.com/hamilton_os) on Twitter/X
- 📧 Join the [mailing lists](../asf/index.rst) for announcements
