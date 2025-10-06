# Welcome to Apache Hamilton
<div align="left">
    <a href="https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g" target="_blank"><img src="https://img.shields.io/badge/Join-Hamilton_Slack-brightgreen?logo=slack" alt="Apache Hamilton Slack"/></a>
    <a href="https://twitter.com/hamilton_os" target="_blank"><img src="https://img.shields.io/twitter/url/http/shields.io.svg?style=social" alt="Twitter"/></a>
    <a href="https://pepy.tech/project/sf-hamilton" target="_blank"><img src="https://pepy.tech/badge/sf-hamilton" alt="Total Downloads"/></a>
    <a href="https://pepy.tech/project/sf-hamilton" target="_blank"><img src="https://static.pepy.tech/badge/sf-hamilton/month" alt="Total Monthly Downloads"/></a>
</div>

Apache Hamilton (incubating) is a general-purpose framework to write dataflows using regular Python functions. At the core, each function defines a transformation and its parameters indicates its dependencies. Apache Hamilton automatically connects individual functions into a [Directed Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph) (DAG) that can be executed, visualized, optimized, and reported on.
Apache Hamilton also comes with a [UI](hamilton-ui/index.rst) to visualize, catalog, and monitor your dataflows.

```{figure} ./_static/abc.png
:scale: 50
:align: center

The ABC of Apache Hamilton
```

# Why should you use Apache Hamilton (incubating)?
**Facilitate collaboration**. By focusing on functions, Apache Hamilton avoids sprawling code hierarchy and generates flat dataflows. Well-scoped functions make it easier to add features, complete code reviews, debug pipeline failures, and hand-off projects. Visualizations can be generated directly from your code to better understand and document it.
Integration with the [Apache Hamilton UI](hamilton-ui/index.rst) allows you to track lineage, catalog code & artifacts, and monitor your dataflows.

**Reduce development time**. Apache Hamilton dataflows are reusable across projects and context (e.g., pipeline vs. web service). The benefits of developing robust and well-tested solutions are multiplied by reusability. Off-the-shelf dataflows are available on the [Apache Hamilton Hub](https://hub.dagworks.io/).

**Own your platform**. Apache Hamilton helps you integrate the frameworks and tools of your stack. Apache Hamilton's features are easy to extend and customize to your needs. This flexibility enables self-serve designs and ultimately reduces the risks of vendor lock-in.

**Scale your dataflow**. Apache Hamilton separates transformation logic from execution, allowing you to seamlessly scale via remote execution (AWS, Modal, etc.) and specialized computation engines (Spark, Ray, duckdb etc.). Apache Hamilton was battle tested under intensive enterprise data workloads.

Here's a quick overview of benefits that Apache Hamilton provides as compared to other tools:

| Feature                                   | Apache Hamilton | Macro orchestration systems (e.g. Airflow) | Feast | dbt | Dask |
|-------------------------------------------|:---:|:---------------------------------------------:|:-----:|:---:|:----:|
| Execute a graph of data transformations   | ✅  |                   ✅                          |   ❌  | ✅  |  ✅   |
| Can visualize lineage easily              | ✅  |                   ❌                          |   ❌  | ✅  |  ✅   |
| Can model GenerativeAI/LLM based workflows| ✅  |                   ❌                          |   ❌  | ❌  |  ❌   |
| Is a feature store                        | ❌  |                   ❌                          |   ✅  | ❌  |  ❌   |
| Helps you structure your code base        | ✅  |                   ❌                          |   ❌  | ✅  |  ❌   |
| Is just a library                         | ✅  |                   ❌                          |   ❌  | ❌  |  ✅   |
| Runs anywhere python runs                 | ✅  |                   ❌                          |   ❌  | ❌  |  ✅   |
| Documentation friendly                    | ✅  |                   ❌                          |   ❌  | ❌  |  ❌   |
| Code is always unit testable              | ✅  |                   ❌                          |   ❌  | ❌  |  ❌   |

# Architecture Overview

The following diagram gives a simplified overview of the main components of Apache Hamilton.

![](./_static/architecture_overview.png)

**Functions & Module**. Transformations are regular Python functions organized into modules. Functions must be type-annotated, but hold no dependency with Apache Hamilton and can be reused outside of it.

**Driver & FunctionGraph**. The `Driver` will automatically assemble the `FunctionGraph` from the modules given. The `Driver` can be configured to modify and extend the execution behavior (e.g., remote execution, monitoring, webhooks, caching).

**Visualization**. The `FunctionGraph` can be visualized without executing code. This coupling ensures visualizations always match the code from modules.

**Execution**. When requesting variables, the `Driver` establishes an execution plan to only compute the required functions. Then, results are gathered and returned to the user.

# Who is using Apache Hamilton?
![](./_static/hamilton_users.jpg)

Multiple companies are doing cool stuff with Apache Hamilton! Come chat with members of the community and the development team on [Slack](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g):

* **Wealth.com** - Async Python LLM document processing pipelines
* **Wren.ai** - Async RAG pipelines
* **Oxehealth** - Multi-modal prediction
* **PupPilot** - Async python LLM transcript processing pipelines
* **Stitch Fix** — Time series forecasting
* **British cycling** — Telemetry analysis
* **Joby** - Flight data processing
* **Transfix** - Online featurization and prediction
* **IBM** - Internal search and ML pipelines
* **Ascena** - Feature engineering
* **Adobe** - Prompt engineering research
* **Axiom Cloud** - IoT data processing
* **Oak Ridge & PNNL** - [Naturf project](https://github.com/IMMM-SFA/naturf/tree/feature/nodes)
* **Habitat** - Time-series feature engineering
* **UK Government Digital Service** - National feedback pipeline (processing & analysis)
* **Railoify** - Orchestrate pandas code
* **Lexis Nexis** - Feature processing and lineage
* **Opendoor** - Manage PySpark pipelines
* **KI** - Feature engineering
* **Kora Money** - DS/ML Workflows
* **Capitec Bank** - Financial decisions
* **Best Egg** - Feature engineering
* **RTV Euro AGD** - General feature engineering & machine learning

# Testimonials

<link rel="stylesheet" type="text/css" href="_static/testimonials.css">
<div class="testimonial-container">
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"Apache Hamilton provides a modular and compatible framework that has significantly empowered our data science team. We've been able to build robust and flexible data pipelines with ease. The documentation is thorough and regularly updated... Even with no prior experience with the package, our team successfully migrated one of our legacy data pipelines to the Apache Hamilton structure within a month. This transition has greatly enhanced our productivity, enabling us to focus more on feature engineering and model iteration while Apache Hamilton's DAG approach seamlessly manages data lineage.<br/>I highly recommend Apache Hamilton to data professionals looking for a reliable, standardized solution for creating and managing data pipelines."</p>
                <h4>Yuan Liu</h4>
                <span>DS, Kora Financial</span>
            </div>
        </div>
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"How (with good software practices) do you orchestrate a system of asynchronous LLM calls, but where some of them depend on others? How do you build such a system so that it’s modular and testable? At wealth.com we've selected Apache Hamilton to help us solve these problems and others. And today our product, Ester AI, an AI legal assistant that extracts information from estate planning documents, is running in production with Apache Hamilton under the hood."</p>
                <h4>Kyle Pounder</h4>
                <span>CTO, Wealth.com</span>
            </div>
        </div>
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"Apache Hamilton is simplicity. Its declarative approach to defining pipelines (as well as the UI to visualize them) makes testing and modifying the code easy, and onboarding is quick and painless. Since using Apache Hamilton, we have improved our efficiency of both developing new functionality and onboarding new developers to work on the code. We deliver solutions more quickly than before."</p>
                <h4>Michał Siedlaczek</h4>
                <span>Senior DS/SWE, IBM</span>
            </div>
        </div>
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"...The companion Apache Hamilton UI has taken the value proposition up enormously with the ability to clearly show lineage & track execution times, covering a major part of our observability needs"</p>
                <h4>Fran Boon</h4>
                <span>Director, Oxehealth.com</span>
            </div>
        </div>
        <div class="testimonial-card">
            <div class="testimonial-content">
                <p>"Many thanks to writing such a great library. We are very excited about it and very pleased with so many decisions you've made. 🙏"</p>
                <h4>Louwrens</h4>
                <span>Software Engineer, luoautomation.com</span>
            </div>
        </div>
</div>
