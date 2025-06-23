<div align="center">
   <h1><img src="https://github.com/apache/hamilton/assets/2328071/feb6abaa-b6d5-4271-a320-0ae4a18d8aa7" width="50"/> Apache Hamilton — portable & expressive <br> data transformation DAGs</h1>
   <a href='https://hamilton.apache.org/?badge=latest'>
      <img src='https://readthedocs.org/projects/hamilton/badge/?version=latest' alt='Documentation Status' />
   </a><a href="https://www.python.org/downloads/" target="_blank">
      <img src="https://img.shields.io/badge/python-3.8|%203.9|%203.10|%203.11|%203.12-blue.svg" alt="Python supported"/>
   </a>
   <a href="https://pypi.org/project/sf-hamilton/" target="_blank">
      <img src="https://badge.fury.io/py/sf-hamilton.svg" alt="PyPi Version"/>
   </a>
   <a href="https://pepy.tech/project/sf-hamilton" target="_blank">
      <img src="https://pepy.tech/badge/sf-hamilton" alt="Total Downloads"/>
   </a>
   <a href="https://pepy.tech/project/sf-hamilton" target="_blank">
      <img src="https://static.pepy.tech/badge/sf-hamilton/month" alt="Total Monthly Downloads"/>
   </a>
   <br/>
   <a target="_blank" href="https://linkedin.com/showcase/dagster" style="background:none">
      <img src="https://img.shields.io/badge/DAGWorks-Follow-purple.svg?logo=linkedin" />
   </a>
   <a href="https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g" target="_blank">
      <img src="https://img.shields.io/badge/Apache Hamilton-Join-purple.svg?logo=slack" alt="Apache Hamilton Slack"/>
   </a>
   <a href="https://twitter.com/hamilton_os" target="_blank">
      <img src="https://img.shields.io/badge/HamiltonOS-Follow-purple.svg?logo=X"/>
   </a>
   <a href="https://twitter.com/dagworks" target="_blank">
      <img src="https://img.shields.io/badge/DAGWorks-Follow-purple.svg?logo=X"/>
   </a>
</div>
<br></br>

Apache Hamilton (incubating) is a lightweight Python library for directed acyclic graphs (DAGs) of data transformations. Your DAG is **portable**; it runs anywhere Python runs, whether it's a script, notebook, Airflow pipeline, FastAPI server, etc. Your DAG is **expressive**; Apache Hamilton has extensive features to define and modify the execution of a DAG (e.g., data validation, experiment tracking, remote execution).

To create a DAG, write regular Python functions that specify their dependencies with their parameters. As shown below, it results in readable code that can always be visualized. Apache Hamilton loads that definition and automatically builds the DAG for you!

<div align="center">
  <img src="./docs/_static/abc_highlight.png" alt="Create a project" width="65%"/>
</div>
<div align="center">
   Functions <code>B()</code> and <code>C()</code> refer to function <code>A</code> via their parameters
</div>
<br>

Apache Hamilton brings modularity and structure to any Python application moving data: ETL pipelines, ML workflows, LLM applications, RAG systems, BI dashboards, and the [Apache Hamilton UI](https://hamilton.apache.org/concepts/ui) allows you to automatically visualize, catalog, and monitor execution.

> Apache Hamilton is great for DAGs, but if you need loops or conditional logic to create an LLM agent or a simulation, take a look at our sister library  [Burr](https://github.com/apache/burr) 🤖 .


# Installation

Apache Hamilton supports Python 3.8+. We include the optional `visualization` dependency to display our Apache Hamilton DAG. For visualizations, [Graphviz](https://graphviz.org/download/) needs to be installed on your system separately.

```bash
pip install "sf-hamilton[visualization]"
```

To use the Apache Hamilton UI, install the `ui` and `sdk` dependencies.

```bash
pip install "sf-hamilton[ui,sdk]"
```

To try Apache Hamilton in the browser, visit [www.tryhamilton.dev](https://www.tryhamilton.dev/?utm_source=README)

# Why use Apache Hamilton?

Data teams write code to deliver business value, but few have the resources to standardize practices and provide quality assurance. Moving from proof-of-concept to production and cross-function collaboration (e.g., data science, engineering, ops) remain challenging for teams, big or small. Apache Hamilton is designed to help throughout a project's lifecycle:

- **Separation of concerns**. Apache Hamilton separates the DAG "definition" and "execution" which lets data scientists focus on solving problems and engineers manage production pipelines.

- **Effective collaboration**. The [Apache Hamilton UI provides a shared interface](https://hamilton.apache.org/hamilton-ui/ui/) for teams to inspect results and debug failures throughout the development cycle.

- **Low-friction dev to prod**. Use `@config.when()` to modify your DAG between execution environments instead of error-prone `if/else` feature flags. The notebook extension prevents the pain of migrating code from a notebook to a Python module.

- **Portable transformations**. Your DAG is [independent of infrastructure or orchestration](https://blog.dagworks.io/publish/posts/detail/145543927?referrer=%2Fpublish%2Fposts), meaning you can develop and debug locally and reuse code across contexts (local, Airflow, FastAPI, etc.).

- **Maintainable DAG definition**. Apache Hamilton [automatically builds the DAG from a single line of code whether it has 10 or 1000 nodes](https://hamilton.apache.org/concepts/driver/). It can also assemble multiple Python modules into a pipeline, encouraging modularity.

- **Expressive DAGs**. [Function modifiers](https://hamilton.apache.org/concepts/function-modifiers/) are a unique feature to keep your code [DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself) and reduce the complexity of maintaining large DAGs. Other frameworks inevitably lead to code redundancy or bloated functions.

- **Built-in coding style**. The Apache Hamilton DAG is [defined using Python functions](https://hamilton.apache.org/concepts/node/), encouraging  modular, easy-to-read, self-documenting, and unit testable code.

- **Data and schema validation**. Decorate functions with `@check_output` to validate output properties, and raise warnings or exceptions. Add the `SchemaValidator()` adapter to automatically inspect dataframe-like objects (pandas, polars, Ibis, etc.) to track and validate their schema.

- **Built for plugins**. Apache Hamilton is designed to play nice with all tools and provides the right abstractions to create custom integrations with your stack. Our lively community will help you build what you need!


# Apache Hamilton UI

You can track the execution of your Apache Hamilton DAG in the [Apache Hamilton UI](https://hamilton.apache.org/hamilton-ui/ui/). It automatically populates a data catalog with lineage / tracing and provides execution observability to inspect results and debug errors. You can run it as a [local server](https://hamilton.apache.org/hamilton-ui/ui/#local-mode) or a [self-hosted application using Docker](https://hamilton.apache.org/hamilton-ui/ui/#docker-deployed-mode).

<p align="center">
  <img src="./docs/_static/hamilton_1.jpeg" alt="Description1" width="30%" style="margin-right: 20px;"/>
  <img src="./docs/_static/hamilton_2.jpeg" alt="Description2" width="30%" style="margin-right: 20px;"/>
  <img src="./docs/_static/hamilton_3.jpeg" alt="Description3" width="30%"/>
</p>
<p align="center">
  <em>DAG catalog, automatic dataset profiling, and execution tracking</em>
</p>


## Get started with the Apache Hamilton UI

1. To use the Apache Hamilton UI, install the dependencies (see `Installation` section) and start the server with

   ```bash
   hamilton ui
   ```

2. On the first connection, create a `username` and a new project (the `project_id` should be `1`).

<div align="center">
  <img src="./docs/_static/new_project.png" alt="Create a project" width="70%"/>
</div>
<br>

3. Track your Apache Hamilton DAG by creating a `HamiltonTracker` object with your `username` and `project_id` and adding it to your `Builder`. Now, your DAG will appear in the UI's catalog and all executions will be tracked!

   ```python
   from hamilton import driver
   from hamilton_sdk.adapters import HamiltonTracker
   import my_dag

   # use your `username` and `project_id`
   tracker = HamiltonTracker(
      username="my_username",
      project_id=1,
      dag_name="hello_world",
   )

   # adding the tracker to the `Builder` will add the DAG to the catalog
   dr = (
      driver.Builder()
      .with_modules(my_dag)
      .with_adapters(tracker)  # add your tracker here
      .build()
   )

   # executing the `Driver` will track results
   dr.execute(["C"])
   ```

# Documentation & learning resources

* 📚 See the [official documentation](https://hamilton.apache.org/) to learn about the core concepts of Apache Hamilton.

* 👨‍🏫 Consult the [examples on GitHub](https://github.com/apache/hamilton/tree/main/examples) to learn about specific features or integrations with other frameworks.

* 📰 The [DAGWorks blog](https://blog.dagworks.io/) includes guides about how to build a data platform and narrative tutorials.

* 📺 Find video tutorials on the [DAGWorks YouTube channel](https://www.youtube.com/@DAGWorks-Inc)

* 📣 Reach out via the [Apache Hamilton Slack community](https://join.slack.com/t/hamilton-opensource/shared_invite/zt-2niepkra8-DGKGf_tTYhXuJWBTXtIs4g) for help and troubleshooting


# How does Apache Hamilton compare to X?

Apache Hamilton is not an orchestrator ([you might not need one](https://blog.dagworks.io/p/lean-data-automation-a-principal)), nor a feature store ([but you can use it to build one!](https://blog.dagworks.io/p/featurization-integrating-hamilton)). Its purpose is to help you structure and manage data transformations. If you know dbt, Apache Hamilton does for Python what dbt does for SQL.

Another way to frame it is to think about the different layers of a data stack. Apache Hamilton is at the **asset layer**. It helps you organize data transformations code (the **expression layer**), manage changes, and validate & test data.

<div align="center" style="width: 100%">
   <table>
      <colgroup>
         <col style="width: 20%">
         <col style="width: 40%">
         <col style="width: 40%">
      </colgroup>
      <thead>
         <tr>
               <th>Layer</th>
               <th>Purpose</th>
               <th>Example Tools</th>
         </tr>
      </thead>
      <tbody>
         <tr>
               <td>Orchestration</td>
               <td>Operational system for the creation of assets</td>
               <td>Airflow, Metaflow, Prefect, Dagster</td>
         </tr>
         <tr>
               <td>Asset</td>
               <td>Organize expressions into meaningful units <br> (e.g., dataset, ML model, table)</td>
               <td><b>Apache Hamilton</b>, dbt, dlt, SQLMesh, <a href="https://github.com/apache/burr">Burr</a></td>
         </tr>
         <tr>
               <td>Expression</td>
               <td>Language to write data transformations</td>
               <td>pandas, SQL, polars, Ibis, LangChain</td>
         </tr>
         <tr>
               <td>Execution</td>
               <td>Perform data transformations</td>
               <td>Spark, Snowflake, DuckDB, RAPIDS</td>
         </tr>
         <tr>
               <td>Data</td>
               <td>Physical representation of data, inputs and outputs</td>
               <td>S3, Postgres, file system, Snowflake</td>
         </tr>
      </tbody>
   </table>
</div>

See our page on [Why use Apache Hamilton?](https://hamilton.apache.org/get-started/why-hamilton/) and framework [code comparisons](https://hamilton.apache.org/code-comparisons/) for more information.

# 📑 License

Apache Hamilton is released under the Apache 2.0 License. See [LICENSE](https://github.com/apache/hamilton/blob/main/LICENSE.md) for details.


# 🌎 Community
## 👨‍💻 Contributing
We're very supportive of changes by new contributors, big or small! Make sure to discuss potential changes by creating an issue or commenting on an existing one before opening a pull request. Good first contributions include creating an example or an integration with your favorite Python library!

 To contribute, checkout our [contributing guidelines](https://github.com/apache/hamilton/blob/main/CONTRIBUTING.md), our [developer setup guide](https://github.com/apache/hamilton/blob/main/developer_setup.md), and our [Code of Conduct](https://github.com/apache/hamilton/blob/main/CODE_OF_CONDUCT.md).


## 😎 Used by
Apache Hamilton was started at Stitch Fix before the original creators founded DAGWorks Inc! The library is battle-tested and has been supporting production use cases since 2019.

>Read more about the [origin story](https://multithreaded.stitchfix.com/blog/2021/10/14/functions-dags-hamilton/).


* [Stitch Fix](https://www.stitchfix.com/) — Time series forecasting
* [UK Government Digital Services](https://github.com/alphagov/govuk-feedback-analysis) — National feedback pipeline (processing & analysis)
* [IBM](https://www.ibm.com/) — Internal search and ML pipelines
* [Opendoor](https://www.opendoor.com/) — Manage PySpark pipelines
* [Lexis Nexis](https://www.lexisnexis.com/en-us/home.page) — Feature processing and lineage
* [Adobe](https://www.adobe.com/) — Prompt engineering research
* [WrenAI](https://github.com/Canner/WrenAI) — async text-to-SQL workflows
* [British Cycling](https://www.britishcycling.org.uk/) — Telemetry analysis
* [Oak Ridge & PNNL](https://pnnl.gov/) — Naturf project
* [ORNL](https://www.ornl.gov/)
* [Federal Reserve Board](https://www.federalreserve.gov/)
* [Joby Aviation](https://www.jobyaviation.com/) — Flight data processing
* [Two](https://www.two.inc/)
* [Transfix](https://transfix.io/) — Online featurization and prediction
* [Railofy](https://www.railofy.com) — Orchestrate pandas code
* [Habitat Energy](https://www.habitat.energy/) — Time-series feature engineering
* [KI-Insurance](https://www.ki-insurance.com/) — Feature engineering
* [Ascena Retail](https://www.ascena.com/) — Feature engineering
* [NaroHQ](https://www.narohq.com/)
* [EquipmentShare](https://www.equipmentshare.com/)
* [Everstream.ai](https://www.everstream.ai/)
* [Flectere](https://flectere.net/)
* [F33.ai](https://f33.ai/)
* [Kora Money](https://www.koramoney.com)
* [Capitec Bank](https://www.capitecbank.co.za/)
* [Best Egg](https://bestegg.com/)
* [RTV Euro AGD](https://www.euro.com.pl/)
* [Wealth.com](https://www.wealth.com/)
* [wren.ai](https://wren.ai/)

## 🤝 Code Contributors
[![Contributors](https://contrib.rocks/image?repo=dagworks-inc/hamilton)](https://github.com/apache/hamilton/graphs/contributors)


## 🙌 Special Mentions & 🦟 Bug Hunters

Thanks to our awesome community and their active involvement in the Apache Hamilton library.

[Nils Olsson](https://github.com/nilsso), [Michał Siedlaczek](https://github.com/elshize), [Alaa Abedrabbo](https://github.com/AAbedrabbo), [Shreya Datar](https://github.com/datarshreya), [Baldo Faieta](https://github.com/baldofaieta), [Anwar Brini](https://github.com/AnwarBrini), [Gourav Kumar](https://github.com/gms101), [Amos Aikman](https://github.com/amosaikman), [Ankush Kundaliya](https://github.com/akundaliya), [David Weselowski](https://github.com/j7zAhU), [Peter Robinson](https://github.com/Peter4137), [Seth Stokes](https://github.com/sT0v), [Louis Maddox](https://github.com/lmmx), [Stephen Bias](https://github.com/s-ducks), [Anup Joseph](https://github.com/AnupJoseph), [Jan Hurst](https://github.com/janhurst), [Flavia Santos](https://github.com/flaviassantos), [Nicolas Huray](https://github.com/nhuray), [Manabu Niseki](https://github.com/ninoseki), [Kyle Pounder](https://github.com/kpounder), [Alex Bustos](https://github.com/bustosalex1), [Andy Day](https://github.com/adayNU), [Alexander Cai](https://github.com/adzcai), [Nils Müller-Wendt](https://github.com/ChronoJon), [Paul Larsen](https://github.com/munichpavel), [
Kemal Eren](https://github.com/kemaleren), [Jernej Frank](https://github.com/jernejfrank), [Noah Ridge](https://github.com/noahridge)

# 🎓 Citations
We'd appreciate citing Apache Hamilton by referencing one of the following:

```bibtex
@inproceedings{DBLP:conf/vldb/KrawczykI22,
  title     = {Hamilton: a modular open source declarative paradigm for high level
               modeling of dataflows},
  author    = {Stefan Krawczyk and Elijah ben Izzy},
  editor    = {Satyanarayana R. Valluri and Mohamed Za{\"{\i}}t},
  booktitle = {1st International Workshop on Composable Data Management Systems,
               CDMS@VLDB 2022, Sydney, Australia, September 9, 2022},
  year      = {2022},
  url       = {https://cdmsworkshop.github.io/2022/Proceedings/ShortPapers/Paper6\_StefanKrawczyk.pdf},
  timestamp = {Wed, 19 Oct 2022 16:20:48 +0200},
  biburl    = {https://dblp.org/rec/conf/vldb/KrawczykI22.bib},
  bibsource = {dblp computer science bibliography, https://dblp.org}
}
```
```bibtex
@inproceedings{CEURWS:conf/vldb/KrawczykIQ22,
  title     = {Hamilton: enabling software engineering best practices for data transformations via generalized dataflow graphs},
  author    = {Stefan Krawczyk and Elijah ben Izzy and Danielle Quinn},
  editor    = {Cinzia Cappiello and Sandra Geisler and Maria-Esther Vidal},
  booktitle = {1st International Workshop on Data Ecosystems co-located with 48th International Conference on Very Large Databases (VLDB 2022)},
  pages     = {41--50},
  url       = {https://ceur-ws.org/Vol-3306/paper5.pdf},
  year      = {2022}
}
```

# 📚 Libraries built on / for Apache Hamilton
* [Hypster](https://github.com/gilad-rubin/hypster) - hyperparameter management
* [DSP Decision Engine](https://github.com/capitec/dsp-decision-engine) - decision trees
* [NaturF](https://github.com/IMMM-SFA/naturf/) - library for data transformation for weather forecasting
* [WrenAI](https://github.com/Canner/WrenAI) - RAG
* [FlowerPower](https://github.com/legout/flowerpower/) - Scheduler for Apache Hamilton
