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

[1.0.0]: https://github.com/apache/hamilton/releases/tag/claude-plugin-v1.0.0
