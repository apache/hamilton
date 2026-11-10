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
covers: hamilton/plugins/h_openlineage.py, hamilton/io/utils.py, hamilton/plugins/pandas_extensions.py, tests/plugins/test_h_openlineage.py, tests/plugins/test_pandas_extensions.py, tests/io/test_utils.py
---
# OpenLineage events and SQL lineage

A user's runs emit OpenLineage events for each node, with the datasets loaders read and savers write, including the tables a SQL query touches.

## How a user reaches it

- `driver.Builder().with_adapters(h_openlineage.OpenLineageAdapter(client, namespace, job_name))`, after `pip install apache-hamilton[openlineage]`.
- pandas SQL loaders and savers (`from_.sql`, `to.sql`), whose metadata carries the tables the lineage reports.

## Scenarios

### openlineage
Run: `test -n "$HAMILTON_TEST_POSTGRES_URL" || { echo 'needs a PostgreSQL server named by HAMILTON_TEST_POSTGRES_URL; verify help openlineage says how to start one' >&2; exit 3; }; uv sync --group test --extra openlineage && uv pip install psycopg2-binary && uv run pytest tests/io/test_utils.py tests/plugins/test_pandas_extensions.py tests/plugins/test_h_openlineage.py || exit $(($? == 3 ? 1 : $?))`
Proves: the OpenLineage adapter, the pandas SQL loaders' lineage, and `hamilton.io.utils` pass against a real PostgreSQL server, as CI's *Test openlineage* step runs them.

## Gotchas

- Its scenario is the suite's `openlineage` scenario word for word; keep the two identical when CI's step changes.
- It needs a PostgreSQL server named by `HAMILTON_TEST_POSTGRES_URL`, as CI's service gives it. Start a disposable local one with `docker run --rm -d --name hamilton-pg -p 5432:5432 -e POSTGRES_USER=hamilton -e POSTGRES_PASSWORD=hamilton -e POSTGRES_DB=sales postgres:16-alpine`, export `HAMILTON_TEST_POSTGRES_URL=postgresql+psycopg2://hamilton:hamilton@localhost:5432/sales`, and `docker stop hamilton-pg` afterwards.
- Without that variable the `postgres_schema` fixture (`tests/conftest.py`) skips every SQL test and the rest would pass on less than CI checks, so the scenario exits 3 (unreachable) instead.
- The fixture creates one throwaway schema per test and drops it, so it leaves the server clean; still point it at a disposable server, never a shared one.
- Every scenario runs CI's own `uv sync`, which is exact: it removes what the step does not name, so `.venv` ends shaped like the last scenario driven. Two drives at once in one checkout share that `.venv` and collide; run side by side only from separate worktrees.
