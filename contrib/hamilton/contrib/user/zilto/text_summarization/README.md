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

# Purpose of this module

This module implements a dataflow to summarize text hitting the OpenAI API.

You can pass in PDFs, or just text and it will get chunked and summarized by the OpenAI API.

# Configuration Options
This module can be configured with the following options:
 - {"file_type":  "pdf"} to read PDFs.
 - {"file_type":  "text"} to read a text file.
 - {} to have `raw_text` be passed in.

# Limitations

This module is limited to OpenAI.

It does not check the context length, so it may fail if the context is too long.
