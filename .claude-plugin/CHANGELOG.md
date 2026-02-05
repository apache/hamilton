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

# Changelog

All notable changes to the Hamilton Claude Code plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-02-04

### Changed (Breaking)
- **Plugin location**: Moved from `.claude/plugins/hamilton/` to `.claude-plugin/` at repo root
  - `.claude/` is now reserved for user configuration only
  - Simpler installation: `claude plugin install ./.claude-plugin --scope user`
  - Self-contained plugin structure
- **Split into focused skills**: Reorganized from single monolithic skill into 6 specialized skills:
  - `hamilton-dev-workflow` - Systematic 5-step development workflow (NEW)
  - `hamilton-core` - Core patterns, decorators, testing, debugging
  - `hamilton-scale` - Async, Ray, Dask, Spark patterns
  - `hamilton-llm` - LLM and RAG workflows
  - `hamilton-observability` - Monitoring, tracking, lineage
  - `hamilton-integrations` - Airflow, FastAPI, Streamlit, etc.

### Added
- **hamilton-dev-workflow skill**: Systematic workflow for building Hamilton DAGs
  - Step 1: Natural language → DOT graph (token-efficient DAG design)
  - Step 2: DOT graph → Function signatures + docstrings
  - Step 3: Validate DAG with Hamilton CLI (`hamilton build`)
  - Step 4: TDD implementation (implement node-by-node with tests)
  - Step 5: Pragmatic type annotations (use `Any` + MonkeyType)
  - Optimized for LLMs: structured, incremental, validatable approach
  - Avoids monolithic implementation and "spaghetti code"

### Fixed
- Installation instructions now reference correct `.claude-plugin/` path
- DOT graph examples now show correct data flow direction (upstream → downstream)

### Documentation
- New workflow-based development guide
- Updated README.md with simplified installation
- Improved contributor documentation

## [1.0.0] - 2025-01-31

### Added
- Initial release of Hamilton Claude Code plugin
- Comprehensive skill for Hamilton DAG development
- Support for creating new Hamilton modules with best practices
- Function modifier guidance (@parameterize, @config.when, @extract_columns, @check_output, etc.)
- Code conversion assistance (Python scripts → Hamilton modules)
- DAG visualization and understanding
- Debugging assistance for common issues
- Data quality validation patterns
- LLM/RAG workflow examples
- Feature engineering patterns
- Integration examples:
  - Airflow
  - FastAPI
  - Streamlit
  - Jupyter notebooks
- Parallel execution patterns (ThreadPool, Ray, Dask, Spark)
- Caching strategies
- Testing guidance

### Documentation
- Comprehensive SKILL.md with all Hamilton patterns
- examples.md with 60+ production-ready code examples
- README.md with installation and usage instructions
- Plugin manifest (plugin.json) and marketplace (marketplace.json)
