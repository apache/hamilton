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

# Apache Hamilton Language Server (`hamilton_lsp`)

> **Disclaimer**
>
> Apache Hamilton is an effort undergoing incubation at the Apache Software Foundation (ASF), sponsored by the Apache Incubator PMC.
>
> Incubation is required of all newly accepted projects until a further review indicates that the infrastructure, communications, and decision making process have stabilized in a manner consistent with other successful ASF projects.
>
> While incubation status is not necessarily a reflection of the completeness or stability of the code, it does indicate that the project has yet to be fully endorsed by the ASF.

This is an implementation of the [Language Server Protocol](https://microsoft.github.io/language-server-protocol/) to provide a rich IDE experience when creating Apache Hamilton dataflows.

It currently powers the Apache Hamilton VSCode extension and could be integrated into other IDEs.

# Building from source

This package uses [flit](https://flit.pypa.io/) as its build backend (declared
in `pyproject.toml`). To build the source distribution and wheel from a source
checkout:

```bash
# from the dev_tools/language_server directory (the package root)
python -m pip install flit
flit build --no-use-vcs
# artifacts are written to dist/
```

`flit build` produces both the `.tar.gz` source distribution and the
`.whl` wheel. `--no-use-vcs` selects files from the working tree rather than
git, which is what you want when building from an unpacked source release.

# License

The code here is licensed under the Apache 2.0 license. See the main repository [LICENSE](../../LICENSE) for details.
