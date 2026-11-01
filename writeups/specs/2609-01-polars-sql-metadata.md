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

# Definition: Polars database I/O records SQL metadata (apache/hamilton#1740)

## 1. Intent
- **Problem:** A team reads `orders` with `PolarsDatabaseReader` and writes a report table with `PolarsDatabaseWriter` against a SQLAlchemy Engine, and runs Hamilton with `OpenLineageAdapter(sql_dataset_identity="datasource")` as #1720 introduced. Lineage for those nodes is wrong: both classes describe database I/O with `get_file_and_dataframe_metadata(self.query | self.table_name, df)` (`polars_post_1_0_0_extensions.py:810`, `:850`; `polars_pre_1_0_0_extension.py:771`, `:811`), so there is no `sql_metadata`, datasource mode cannot identify the database, and the adapter emits fake FileSystem datasets (a read named after the node with the SQL text as its URI) and no `sql` job facet. Reproduced: `sorted(md) == ['dataframe_metadata', 'file_metadata']`, `md["file_metadata"]["path"] == "SELECT * FROM orders"`. The issue text predates #1720's final form; the fix follows what #1720 merged — legacy mode stays compatible with existing conventions (ADR `writeups/adr/2609-01-staged-sql-dataset-identity.md`).
- **Appetite:** Small. Four call sites in two Polars plugin files, their tests, and one docs page. No change to shared helpers or the adapter.
- **Out of bounds:**
  - Recognising more connection types in `get_sql_source` (issue item 2: ADBC connections, connectorx URIs, cursors, Sessions) — deferred; those already drop out of lineage with a note, and SQLAlchemy-parsing connectorx SQLite URIs would name the wrong file.
  - Removing `file_metadata` from the Polars database classes — reserved for the major release that flips the `sql_dataset_identity` default.
  - Opening, pushing, or driving a pull request; commenting on #1740. The run ends at a local branch.

## 2. Initial Approach
- **Architecture:**
  - Post-1.0 reader/writer return `{**utils.get_file_and_dataframe_metadata(<query|table_name>, df), **utils.get_sql_metadata(<query|table_name>, rows, db_connection=self.connection, operation="read"|"write")}`. Legacy builders in `h_openlineage.py` check `file_metadata` before `sql_metadata` (`:363`, `:416`), so legacy output is unchanged; datasource mode reads `sql_metadata`.
  - Read rows: `len(df)` only when `df` is a `pl.DataFrame` (with `iter_batches=True` `pl.read_database` returns a generator), else `None`. Write rows: the `int` that `write_database` returns. Pass the count as `results`; do not broaden `get_sql_metadata`'s row counting (`tests/io/test_utils.py` pins `rows is None` for non-frame input).
  - Pre-1.0 reader/writer: keep `file_metadata`; add `get_sql_metadata(<query|table_name>, rows, operation=...)` with no `db_connection`, then set its `notes` to an upgrade message (e.g. "Datasource lineage for Polars database I/O requires polars>=1.0; upgrade polars"). In datasource mode `sql_datasets` returns no dataset and `_sql_lineage` logs the note; verified in a scratch run.
  - The pre-1.0 module imports and its database classes run under the installed Polars 1.41 when given a `sqlite3.Connection` (verified), so they can be exercised directly in tests even though the plugin registry only loads that module for Polars <1.0.
  - Reuse `run_with_lineage` / `FileTransport` harness in `tests/plugins/test_h_openlineage.py:318-333` for end-to-end tests.
  - Work on a local branch `2609/polars-sql-metadata` off `main`. Commit message body carries the release-note line: Polars database I/O now also records `sql_metadata`; default-mode OpenLineage users may see the identity `FutureWarning`, silenced by `sql_dataset_identity="legacy"`.

## 3. Global Invariants

### INV-G1 — The change stops at what this Manifest authorized

Read this Manifest. This is a conformance check: take its intent as given, and do not judge
whether the work was necessary, motivated, or worthwhile.

Done when the work this run added carries nothing the Deliverables, Acceptance Criteria, and
Global Invariants — this one excluded — required, and nothing that nominally serves one of
them while far exceeding the surface the Appetite allows.

Read Problem, Appetite, and Out of bounds as the intent. Read the Deliverables and the other
gates as what the work owes. Read the Initial Approach and Process Guidance as mechanisms that
were *authorized rather than owed* — the ones expected, never the only ones permitted, so work
reaching a Deliverable by a route this Manifest does not name is required by that Deliverable.

Required although no criterion names it: work inherited rather than added — the artifact this
Manifest was synthesized over, and anything arriving from outside the run such as a base branch
merged into the head — and work discharging what a criterion required, including sweeping a
changed rule into every copy and surface that holds it.

FAIL only on work none of the above accounts for. Treat an unclear case as required work, and
leave small, incidental, or imperfect changes inside an artifact already in scope alone.

Why: every other gate states a floor, so a contract bounded on one side only gives an executor
disposed to thoroughness nothing to read as a limit.

Judgment gate.

### INV-G2 — Legacy-mode OpenLineage output for Polars database nodes is unchanged

Done when, for every Polars database reader and writer class in `hamilton/plugins/polars_post_1_0_0_extensions.py` and `hamilton/plugins/polars_pre_1_0_0_extension.py`, the legacy-mode dataset the adapter emits — namespace, name, and the full facet set with values, excluding only timestamp-derived values — is identical on this branch and on `main`. Procedure: in a disposable `git worktree` of `main` and in the branch working tree, run the same script with the repo's `.venv/bin/python` that, against a fresh SQLite file, writes a table with each writer and reads it back with each reader (pre-1.0 classes given a `sqlite3.Connection`, post-1.0 classes given a SQLAlchemy Engine), passes each returned metadata dict through `h_openlineage.create_input_dataset` / `create_output_dataset`, and prints the serialized datasets; the two outputs must match. Also FAIL if the returned metadata on this branch lacks a `file_metadata` key or its `file_metadata` values differ from `main` (timestamps excepted). Remove the worktree afterwards with `git worktree remove --force`.

Why: ADR 2609-01 promises that the default legacy mode emits exactly what earlier releases emitted; the user ruled that this fix must keep that promise.

Deterministic gate.

### INV-G3 — Recording metadata never fails a successful database read or write

Done when no code path added to the Polars database classes' `load_data` / `save_data` can raise after the Polars read or write has succeeded, for any connection form those classes accept (SQLAlchemy Engine, Connection, Session, URL string; `sqlite3` Connection or Cursor; ADBC connections; other DBAPI connections) and for `iter_batches=True` reads that return a generator. Inspect the diff of both plugin files and trace each added call (`len`, `get_sql_metadata`, dict merging, notes assignment) against those inputs; `get_sql_source` already catches inspection errors, so the hiding place is anything computed outside it — row counting especially. The branch's tests must include an `iter_batches=True` read through `PolarsDatabaseReader` that returns without raising.

Judgment gate.

### INV-G4 — Shared SQL helpers and the adapter are untouched

Done when `git diff main --stat -- hamilton/io/utils.py hamilton/plugins/h_openlineage.py` prints nothing.

Why: #1720's merged behaviour is the contract this fix conforms to.

Deterministic gate.

### INV-G5 — Project lint, format and the affected test suites pass

Done when both succeed on the branch working tree: `pre-commit run --files $(git diff --name-only main)` exits 0, and `.venv/bin/python -m pytest tests/plugins/test_polars_extensions.py tests/plugins/test_polars_lazyframe_extensions.py tests/plugins/test_h_openlineage.py tests/io/test_utils.py -q` exits 0 with no test newly skipped relative to `main`. No type-checker is configured for this project (mypy is commented out in `pyproject.toml`), so none is run.

Deterministic gate.

### INV-G6 — The change says what it does

Done when the manifest-dev:review-code skill, activated with dimension=change-intent, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G7 — No mechanical bugs

Done when the manifest-dev:review-code skill, activated with dimension=code-bugs, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G8 — The defect class is closed

Done when the manifest-dev:review-code skill, activated with dimension=defect-class, reports nothing at or above that dimension's threshold. The class: a Hamilton data loader or saver that performs SQL database I/O but describes it with file metadata instead of `sql_metadata`, anywhere under `hamilton/plugins/`.

Judgment gate.

### INV-G9 — Metadata contract stays consistent with #1720

Done when the manifest-dev:review-code skill, activated with dimension=contracts, reports nothing at or above that dimension's threshold. The contract surfaces are the metadata dicts the Polars database classes return, as consumed by `hamilton/plugins/h_openlineage.py` (`sql_datasets`, `create_input_dataset`, `create_output_dataset`) and `hamilton/plugins/h_mlflow.py`.

Judgment gate.

### INV-G10 — Type hints stay sound

Done when the manifest-dev:review-code skill, activated with dimension=type-safety, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G11 — Operational readiness

Done when the manifest-dev:review-code skill, activated with dimension=operational-readiness, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G12 — Maintainability

Done when the manifest-dev:review-code skill, activated with dimension=code-maintainability, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G13 — Simplicity

Done when the manifest-dev:review-code skill, activated with dimension=code-simplicity, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G14 — Design fitness

Done when the manifest-dev:review-code skill, activated with dimension=code-design, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G15 — Testability

Done when the manifest-dev:review-code skill, activated with dimension=code-testability, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G16 — Test quality

Done when the manifest-dev:review-code skill, activated with dimension=test-quality, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G17 — Documentation

Done when the manifest-dev:review-code skill, activated with dimension=docs, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G18 — Prose value

Done when the manifest-dev:review-code skill, activated with dimension=prose-value, reports nothing at or above that dimension's threshold.

Judgment gate.

### INV-G19 — Context-file adherence

Done when the manifest-dev:review-code skill, activated with dimension=context-file-adherence, reports nothing at or above that dimension's threshold.

Judgment gate.

## 4. Process Guidance
- [PG-1] Run the four test files in INV-G5 on `main` before touching tests, so pre-existing failures are known.
- [PG-2] Write each new test first and watch it fail against the current code before changing the plugin (red loop: the current classes return no `sql_metadata`).
- [PG-3] Assert behaviour through the public seams — the classes' `load_data`/`save_data` return values and the events a Hamilton driver emits through `OpenLineageAdapter` — not private helpers.
- [PG-4] Commit only on the local branch `2609/polars-sql-metadata`; never push. Name the mechanism (file metadata used for database I/O) in the commit message.

## 5. Known Assumptions
- [ASM-1] The release-note line lives in the commit message body, since there is no CHANGELOG file and no PR in scope | Default: commit body | Impact if wrong: note moved to wherever the user ships it; no code impact.
- [ASM-2] (auto) The pre-1.0 upgrade note wording | Default: "Datasource lineage for Polars database I/O requires polars>=1.0; upgrade polars" | Impact if wrong: wording edit.
- [ASM-3] Exercising the pre-1.0 classes under Polars 1.41 with a `sqlite3.Connection` stands in for real Polars <1.0 | Default: accepted; real Polars <1.0 is not installable in this environment | Impact if wrong: a pre-1.0-specific behaviour difference in `read_database`/`write_database` return values goes unseen; the metadata code does not depend on it beyond the row-count guard.

## 6. Deliverables
- **Order rationale:** Deliverable 1 carries the approach's main bet (additive metadata keeps legacy output while datasource mode works end-to-end through the real driver); Deliverable 2 reuses its pattern; Deliverable 3 documents both.

### Deliverable 1: Post-1.0 Polars database nodes get datasource lineage

*What it is, and how it is exercised end-to-end:* the post-1.0 `PolarsDatabaseReader`/`PolarsDatabaseWriter` record `sql_metadata`; exercised by a Hamilton driver with `OpenLineageAdapter` running a DAG that saves through `PolarsDatabaseWriter` and loads through `PolarsDatabaseReader` against a SQLite file via a SQLAlchemy Engine, with the emitted events read back from a `FileTransport` log.

#### AC-1.1 — Datasource mode names the SQLite tables read and written

Done when a test on the branch runs a Hamilton driver with `OpenLineageAdapter(..., sql_dataset_identity="datasource")` over a DAG that writes table `orders` with `PolarsDatabaseWriter` and reads `SELECT * FROM orders` with `PolarsDatabaseReader` against a SQLite file through a SQLAlchemy Engine, and asserts from the emitted events: the write's output dataset is namespace `sqlite://{absolute file path}` + name `orders`; the read's input dataset is the same namespace + `orders`; the read's job carries a `sql` facet with the query; no emitted dataset for these nodes has a `storage` facet with `storageLayer="FileSystem"`. The test passes under INV-G5's command.

Deterministic gate.

#### AC-1.2 — Row counts are recorded where they exist

Done when tests on the branch assert that `sql_metadata["rows"]` equals the number of rows read for a plain `PolarsDatabaseReader` read, equals the number of rows written for a `PolarsDatabaseWriter` write, and is `None` for an `iter_batches=True` read, and those tests pass under INV-G5's command.

Deterministic gate.

#### AC-1.3 — Legacy output is pinned by a test

Done when a test on the branch runs the post-1.0 reader and writer through a Hamilton driver with `OpenLineageAdapter` in default (legacy) mode and asserts the exact namespace, name and facet keys of each emitted dataset as they are on `main` (read named after the loader node with `storage`, `dataSource`, `schema` facets; write named after the table with the same facet keys), so reordering the `file_metadata`/`sql_metadata` branches in the adapter would fail it. It passes under INV-G5's command.

Why: the additive design relies on the adapter checking `file_metadata` first; nothing else guards that.

Judgment gate.

### Deliverable 2: Pre-1.0 Polars database nodes stay legacy-only and tell datasource users to upgrade

*What it is, and how it is exercised end-to-end:* the pre-1.0 reader/writer keep file metadata and add a connection-less `sql_metadata` with an upgrade note; exercised by calling the pre-1.0 classes' `load_data`/`save_data` against a SQLite file with a `sqlite3.Connection` and feeding the returned metadata through the adapter in both identity modes.

#### AC-2.1 — Datasource mode emits no dataset and logs the upgrade note

Done when a test on the branch passes metadata returned by the pre-1.0 `PolarsDatabaseReader.load_data` and `PolarsDatabaseWriter.save_data` through `OpenLineageAdapter` (or `h_openlineage._sql_lineage` / `sql_datasets`) in datasource mode and asserts: no input or output dataset is produced for those nodes, and a warning from the `hamilton.plugins.h_openlineage` logger contains text telling the user to upgrade to polars>=1.0. The same test or a sibling asserts that `sql_metadata["source"]` is `None` for both classes. Passes under INV-G5's command.

Deterministic gate.

### Deliverable 3: Docs describe Polars database lineage

*What it is, and how it is exercised end-to-end:* `docs/reference/lifecycle-hooks/OpenLineageAdapter.rst` read by a user choosing an identity mode for a pipeline that uses Polars database materializers.

#### AC-3.1 — A reader learns what each mode does for Polars database I/O

Done when `docs/reference/lifecycle-hooks/OpenLineageAdapter.rst` states, in the sections a reader choosing `sql_dataset_identity` reads (the SQL datasets overview at line ~21 and the legacy-mode description): that the Polars database materializers record the datasource; that in legacy mode they keep their earlier dataset names (the read named after the loader node, the write after the table), unlike the pandas SQL query-read case described there; and that datasource mode for them requires polars>=1.0, with older Polars logging an upgrade note and emitting no dataset. No existing statement on the page is left contradicting these, and the page builds without new Sphinx warnings for that file if a docs build is available (otherwise the evaluator checks the RST syntax by reading it).

Judgment gate.
