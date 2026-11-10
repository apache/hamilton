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
kind: plugin
covers: hamilton/plugins/h_spark.py, hamilton/plugins/h_schema.py, hamilton/plugins/spark_extensions.py, hamilton/plugins/pyspark_pandas_extensions.py, plugin_tests/h_spark
---
# PySpark dataframes

A user builds PySpark DataFrame columns from functions, runs nodes as Spark user-defined functions (UDFs) or on pandas-on-Spark, and tracks dataframe schemas.

## How a user reaches it

- `@h_spark.with_columns(...)`, `@h_spark.select(...)`, and `@h_spark.require_columns(...)`.
- `h_spark.PySparkUDFGraphAdapter()` and `h_spark.SparkKoalasGraphAdapter(...)` as the driver's adapter.
- `h_schema.SchemaValidator` to record and check dataframe schemas.

## Scenarios

### pyspark
Run: `command -v dot >/dev/null || { echo 'needs Graphviz: dot is not on PATH (CI installs graphviz)' >&2; exit 3; }; command -v java >/dev/null || { echo 'needs a Java runtime: java is not on PATH (CI installs default-jre)' >&2; exit 3; }; uv sync --group test --extra pyspark && uv pip install 'pyspark[connect]' 'grpcio' && uv pip install --no-cache --reinstall --strict 'grpcio-status >= 1.48.1' && PYSPARK_SUBMIT_ARGS='--conf spark.sql.ansi.enabled=false pyspark-shell' uv run pytest plugin_tests/h_spark || exit $(($? == 3 ? 1 : $?))`
Proves: the pyspark adapters, `h_spark.with_columns`, and `h_schema` integration tests pass with the `pyspark` extra and Spark Connect, as CI's *Test pyspark* step runs them on Linux.

## Gotchas

- Its scenario is the suite's `pyspark` scenario word for word; keep the two identical when CI's step changes.
- Spark needs a Java runtime that its version supports; a Java Runtime Environment (JRE) newer than that fails at session start, which reads as failed rather than unreachable. CI uses Ubuntu's `default-jre`.
- `PYSPARK_SUBMIT_ARGS` turns ANSI SQL mode off as CI does; without it some casts raise.
- It runs a local Spark session; nothing outside the machine is used.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
