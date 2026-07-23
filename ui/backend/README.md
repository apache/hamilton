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

## Building from source

This package uses [flit](https://flit.pypa.io/) as its build backend (declared
in `pyproject.toml`).

The **source distribution** (`.tar.gz`) is backend-only and builds directly:

```bash
# from the ui/backend directory (the package root)
python -m pip install flit
flit build --no-use-vcs --format sdist
# artifact is written to dist/
```

The **wheel** additionally bundles a compiled frontend, so it requires
Node.js + npm. Build the frontend first, copy it into the package, then
build the wheel:

```bash
# 1. build the frontend (from ui/frontend)
cd ../frontend
npm install
npm run build
npm run licenses     # generates build/THIRD-PARTY-LICENSES.txt

# 2. copy the compiled assets into the backend package
rm -rf ../backend/hamilton_ui/build
cp -r build ../backend/hamilton_ui/build

# 3. build the wheel (from ui/backend)
cd ../backend
flit build --no-use-vcs --format wheel
# artifact is written to dist/
```

The release script `scripts/apache_release_helper.py --package ui` performs all
of these steps automatically.

## License

Apache 2.0. See the [LICENSE](LICENSE) file included with this package for details.

This package is distributed in two forms:

- The **source distribution** (sdist) contains only Apache Hamilton source code,
  licensed under the Apache License, Version 2.0.
- The **binary distribution** (wheel) additionally bundles a compiled frontend
  web application (`hamilton_ui/build/`) built from the TypeScript/React sources
  in `ui/frontend/`. That bundle includes third-party JavaScript dependencies
  (e.g. React, Redux, Chart.js, React Flow), each under permissive licenses
  (MIT, Apache-2.0, BSD, ISC, and similar). The full per-dependency license
  texts and copyright notices are included in the wheel at
  `hamilton_ui/build/THIRD-PARTY-LICENSES.txt`.
