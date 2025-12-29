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

# Apache Hamilton Language Server

Apache Hamilton VSCode uses a [Language Server](https://microsoft.github.io/language-server-protocol/) to build a dataflow from your currently active file.

Current features include:
- view the dataflow
- completion suggestions

## Debugging

You can view the server logs to inspect unexpected behaviors or bugs. The log level will match the `VSCode Log Level`. Set it to `Debug` for further details.

> ⚠
> - If the visualization doesn't update or is slow, close and reopen the activity bar (`ctrl+b`) or the panel (`ctrl+j`)
> - If you encountered freezes, open the command palette `ctrl+p` and use `Developer: Reload Window`.
