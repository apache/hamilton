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

# Apache Hamilton UI: Tracking Server

> **Disclaimer**
>
> Apache Hamilton is an effort undergoing incubation at the Apache Software Foundation (ASF), sponsored by the Apache Incubator PMC.
>
> Incubation is required of all newly accepted projects until a further review indicates that the infrastructure, communications, and decision making process have stabilized in a manner consistent with other successful ASF projects.
>
> While incubation status is not necessarily a reflection of the completeness or stability of the code, it does indicate that the project has yet to be fully endorsed by the ASF.

`apache-hamilton-ui` is the tracking server and web application for visualizing, monitoring, and
debugging Apache Hamilton dataflow DAGs.

## Features

- Visualize Hamilton DAGs and their execution history
- Track inputs, outputs, and runtime metadata for each DAG run
- Compare runs across versions and configurations
- Self-hosted: run locally or deploy on your own infrastructure

## Getting Started

The easiest way to run the UI is via Docker:

```bash
git clone https://github.com/apache/hamilton
cd hamilton/ui
docker-compose up
```

Then open [http://localhost:8242](http://localhost:8242) in your browser.

For full documentation, visit [hamilton.apache.org](https://hamilton.apache.org/) and see the
**Apache Hamilton UI** section.

## Connecting Hamilton to the UI

Install the tracking SDK alongside your Hamilton project:

```bash
pip install "apache-hamilton[sdk]"
```

Then add a `HamiltonTracker` adapter to your driver:

```python
from hamilton_sdk import adapters
from hamilton import driver

tracker = adapters.HamiltonTracker(
    project_id=PROJECT_ID,
    username=YOUR_EMAIL,
    dag_name="my_dag",
)
dr = (
    driver.Builder()
    .with_config(your_config)
    .with_modules(*your_modules)
    .with_adapters(tracker)
    .build()
)
```

## License

Apache 2.0. See the main repository [LICENSE](../../LICENSE) for details.
